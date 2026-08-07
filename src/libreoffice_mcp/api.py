"""REST API for libreoffice-mcp webapp (port 10981)."""

from __future__ import annotations

import json as _json
import logging
import mimetypes
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from . import __version__
from .agentic import execute_plan, llm_enrich_plan, plan_goal
from .bridge import health_summary
from .config import reload_settings, settings
from .env_utils import read_env_file, redact_env, repo_env_path, write_env_updates
from .fleet import discover_fleet_from_docs
from .formats import document_info, suggested_formats
from .headless import convert_batch
from .jobs import enqueue_convert, get_job, list_jobs
from .logging_utils import get_logs
from .pack import pack_markdown_files
from .pdf_ops import merge_pdfs
from .reveal import reveal_path
from .sampling import LoSamplingHandler
from .self_test import run_self_tests
from .skills_catalog import list_bundled_skills, read_skill
from .storage import list_indexed_outputs
from .templates import ensure_builtin_templates, list_templates, merge_and_convert
from .watch_folder import start_watch, stop_watch, watch_status
from .workflows import catalog, run_simple_action, run_workflow

router = APIRouter()
log = logging.getLogger(__name__)
_sampling = LoSamplingHandler()


class ConvertRequest(BaseModel):
    input_path: str = Field(description="Absolute path to source document")
    output_format: str = Field(default="pdf", description="pdf, odt, docx, html, xlsx, csv")


class MergeRequest(BaseModel):
    template: str = Field(description="Template filename (e.g. fleet-board-pack.odt)")
    placeholders: dict[str, str] = Field(default_factory=dict)
    output_format: str = Field(default="pdf")
    output_stem: str | None = Field(default=None, description="Output filename stem (no extension)")


class PackRequest(BaseModel):
    input_paths: list[str] = Field(description="Absolute paths to markdown files")
    title: str = Field(default="Document Pack")
    output_format: str = Field(default="pdf")
    output_stem: str | None = Field(default=None)


class LlmTestRequest(BaseModel):
    provider: str = Field(default="ollama")
    base_url: str | None = None
    model: str | None = None
    api_key: str | None = None


class ActionRunRequest(BaseModel):
    action_id: str
    params: dict[str, Any] = Field(default_factory=dict)


class WorkflowRunRequest(BaseModel):
    workflow_id: str
    params: dict[str, Any] = Field(default_factory=dict)


class AgenticRequest(BaseModel):
    goal: str
    execute: bool = Field(default=False, description="Run first planned step when true")
    params: dict[str, Any] = Field(default_factory=dict)
    use_llm: bool = Field(default=False, description="Enrich plan via Ollama when online")


class BatchConvertRequest(BaseModel):
    input_paths: list[str]
    output_format: str = "pdf"


class PdfMergeRequest(BaseModel):
    input_paths: list[str]
    output_stem: str = "merged"


class WatchRequest(BaseModel):
    watch_path: str
    glob_pattern: str = "*.*"
    output_format: str = "pdf"


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    system_prompt: str = Field(
        default="", description="System prompt composed from skill + personality"
    )
    history: list[ChatMessage] = Field(
        default_factory=list, description="Prior conversation messages"
    )
    execute: bool = Field(default=True, description="Execute planned LibreOffice ops when true")
    params: dict[str, Any] = Field(default_factory=dict)


_LIBREOFFICE_OPS = [
    "status",
    "convert",
    "convert_batch",
    "document_info",
    "merge",
    "list_templates",
    "batch_pack",
    "pdf_merge",
    "watch_start",
    "watch_stop",
    "watch_status",
    "reveal_output",
    "writer_session_status",
    "launch_writer",
    "live_write",
    "live_type",
    "run_macro",
    "run_python_macro",
    "list_macros",
    "bridge_discover",
    "bridge_call",
    "help",
]


def _safe_output_file(name: str) -> Path:
    if not name or name != Path(name).name or ".." in name:
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = settings.output_dir / name
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {name}")
    return path.resolve()


@router.get("/capabilities")
async def api_capabilities() -> dict[str, Any]:
    """Mandatory feature flags — WEBAPP_STANDARDS §1.4."""
    soffice = settings.resolve_soffice()
    bridge = await health_summary()
    return {
        "status": "ok",
        "server": {
            "name": "libreoffice-mcp",
            "version": __version__,
            "fastmcp": "3.3+",
        },
        "tool_surface": {
            "portmanteau": "libreoffice",
            "operations": _LIBREOFFICE_OPS,
            "operation_count": len(_LIBREOFFICE_OPS),
        },
        "features": {
            "headless_convert": soffice is not None,
            "template_merge": True,
            "batch_pack": True,
            "pdf_merge": True,
            "convert_batch": True,
            "file_upload": True,
            "watch_folder": True,
            "document_info": True,
            "persistent_jobs": True,
            "extension_bridge": bool((bridge.get("extension_bridge") or {}).get("online")),
            "openapi_docs": True,
            "local_llm_chat": True,
            "agentic_chat": True,
            "fleet_apps_hub": True,
            "simple_actions": True,
            "complex_workflows": True,
            "agentic_planner": True,
            "sampling": True,
            "agentic_mcp_tool": True,
            "prompts": True,
            "prefab_apps": True,
            "skills": True,
            "webapp_tests": True,
            "live_write": True,
            "live_typewriter": True,
            "writer_session_bridge": True,
            "uno_macros": True,
            "oxt_bridge_extension": True,
        },
        "integrations": {
            "soffice": str(soffice) if soffice else None,
            "extension_bridge_url": settings.extension_bridge_url,
            "central_docs_path": settings.central_docs_path,
            "ollama_base_url": settings.ollama_base_url,
            "sampling": _sampling.status(),
        },
        "runtime": {"transport": "http", "backend_port": settings.port, "frontend_port": 10983},
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/logs")
async def api_logs() -> dict[str, Any]:
    return {"logs": get_logs()}


@router.get("/fleet/apps")
async def api_fleet_apps() -> dict[str, Any]:
    apps = discover_fleet_from_docs()
    return {"apps": [a.model_dump() for a in apps]}


@router.get("/env")
async def api_get_env() -> dict[str, Any]:
    env = read_env_file(repo_env_path())
    defaults = {
        "LIBREOFFICE_MCP_SOFFICE_PATH": settings.soffice_path,
        "LIBREOFFICE_MCP_EXTENSION_BRIDGE_URL": settings.extension_bridge_url,
        "LIBREOFFICE_MCP_CENTRAL_DOCS_PATH": settings.central_docs_path,
        "LIBREOFFICE_MCP_OLLAMA_BASE_URL": settings.ollama_base_url,
        "LIBREOFFICE_MCP_OLLAMA_MODEL": settings.ollama_model,
        "LIBREOFFICE_MCP_LMSTUDIO_BASE_URL": settings.lmstudio_base_url,
        "LIBREOFFICE_MCP_OPENAI_MODEL": settings.openai_model,
    }
    merged = {**defaults, **env}
    return redact_env(merged)


@router.post("/env")
async def api_update_env(request: Request) -> dict[str, Any]:
    body = await request.json()
    if isinstance(body, dict) and "values" in body and isinstance(body["values"], dict):
        updates = body["values"]
    elif isinstance(body, dict):
        updates = body
    else:
        raise HTTPException(status_code=400, detail="Expected JSON object")
    write_env_updates(updates)
    reload_settings()
    log.info("Settings saved to .env")
    return {"ok": True, "message": "Settings saved — reload applied"}


@router.get("/llm/discover")
async def api_llm_discover() -> dict[str, Any]:
    """Probe Ollama (:11434) and LM Studio (:1234)."""
    providers: list[dict[str, Any]] = []

    async def probe(name: str, base: str, tags_path: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                r = await client.get(f"{base.rstrip('/')}{tags_path}")
                if r.is_success:
                    data = r.json()
                    models: list[str] = []
                    if name == "ollama":
                        models = [
                            m.get("name", "") for m in data.get("models", []) if m.get("name")
                        ]
                    elif name == "lmstudio":
                        models = [m.get("id", "") for m in data.get("data", []) if m.get("id")]
                    providers.append(
                        {
                            "id": name,
                            "name": name,
                            "base_url": base,
                            "online": True,
                            "models": models[:20],
                            "chat_endpoint": "ollama" if name == "ollama" else "openai",
                        }
                    )
                    return
        except (httpx.HTTPError, OSError):
            pass
        providers.append(
            {
                "id": name,
                "name": name,
                "base_url": base,
                "online": False,
                "models": [],
                "chat_endpoint": "ollama" if name == "ollama" else "openai",
            }
        )

    await probe("ollama", settings.ollama_base_url, "/api/tags")
    await probe("lmstudio", settings.lmstudio_base_url, "/v1/models")
    return {"providers": providers, "gpu": _detect_gpu()}


def _detect_gpu() -> dict[str, Any]:
    """Probe for NVIDIA GPU via nvidia-smi."""
    try:
        import subprocess

        proc = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            lines = proc.stdout.strip().splitlines()
            gpus = []
            for line in lines[:4]:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 1:
                    gpus.append(
                        {
                            "name": parts[0],
                            "memory": parts[1] if len(parts) > 1 else "",
                            "driver": parts[2] if len(parts) > 2 else "",
                        }
                    )
            return (
                {"detected": True, "count": len(gpus), "devices": gpus}
                if gpus
                else {"detected": False}
            )
    except Exception:
        pass
    return {"detected": False}


@router.post("/test-llm")
async def api_test_llm(body: LlmTestRequest) -> dict[str, Any]:
    provider = body.provider or "ollama"
    if provider == "ollama":
        base = body.base_url or settings.ollama_base_url
        model = body.model or settings.ollama_model
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(
                    f"{base.rstrip('/')}/api/chat",
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": "ping"}],
                        "stream": False,
                    },
                )
                r.raise_for_status()
            return {"ok": True, "provider": provider, "model": model, "message": "Ollama responded"}
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Ollama test failed: {exc}") from exc

    if provider == "openai":
        key = body.api_key or settings.openai_api_key
        if not key:
            raise HTTPException(status_code=400, detail="OpenAI API key required")
        model = body.model or settings.openai_model
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}"},
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": "ping"}],
                        "max_tokens": 5,
                    },
                )
                r.raise_for_status()
            return {"ok": True, "provider": provider, "model": model, "message": "OpenAI responded"}
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"OpenAI test failed: {exc}") from exc

    raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")


@router.get("/skills")
async def api_skills() -> dict[str, Any]:
    return {"success": True, "skills": list_bundled_skills()}


@router.get("/skills/{skill_id}")
async def api_skill_detail(skill_id: str) -> dict[str, Any]:
    skill = read_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill_id}")
    return {"success": True, "skill": skill}


@router.get("/actions")
async def api_actions_catalog() -> dict[str, Any]:
    """Simple one-shot LibreOffice operations for the webapp."""
    data = catalog()
    return {"success": True, **data}


@router.post("/actions/run")
async def api_run_action(body: ActionRunRequest) -> dict[str, Any]:
    result = await run_simple_action(body.action_id, body.params)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Action failed"))
    return {"success": True, **result}


@router.get("/workflows")
async def api_workflows_catalog() -> dict[str, Any]:
    """Multi-step coworker and batch workflows."""
    data = catalog()
    return {
        "success": True,
        "workflows": data["workflows"],
        "defaults": data["defaults"],
        "templates": data["templates"],
    }


@router.post("/workflows/run")
async def api_run_workflow(body: WorkflowRunRequest) -> dict[str, Any]:
    result = await run_workflow(body.workflow_id, body.params)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Workflow failed"))
    return {"success": True, **result}


@router.post("/agentic")
async def api_agentic(body: AgenticRequest) -> dict[str, Any]:
    """Natural-language goal → plan; optional execute + Ollama hint."""
    if body.execute:
        result = await execute_plan(body.goal, params=body.params, execute=True)
    else:
        result = plan_goal(body.goal)
    if body.use_llm and result.get("success"):
        result = await llm_enrich_plan(body.goal, result)
    return result


@router.post("/chat")
async def api_chat(body: ChatRequest) -> dict[str, Any]:
    """Agentic chat — LLM-powered when system_prompt + provider available, else rule-based."""
    if body.system_prompt:
        msgs: list[dict[str, str]] = [{"role": "system", "content": body.system_prompt}]
        for msg in body.history:
            msgs.append({"role": msg.role, "content": msg.content})
        msgs.append({"role": "user", "content": body.message})

        # Try Ollama first, then LM Studio (OpenAI-compat), then OpenAI cloud
        attempts = [
            (settings.ollama_base_url, settings.ollama_model, False),
            (settings.lmstudio_base_url, settings.openai_model, True),
            ("https://api.openai.com/v1", settings.openai_model, True),
        ]
        for base_url, model, is_openai in attempts:
            if not base_url or not model:
                continue
            if (
                is_openai
                and base_url == "https://api.openai.com/v1"
                and not settings.openai_api_key
            ):
                continue
            headers = {}
            if is_openai and settings.openai_api_key:
                headers["Authorization"] = f"Bearer {settings.openai_api_key}"
            try:
                u = f"{base_url.rstrip('/')}/{'v1/chat/completions' if is_openai else 'api/chat'}"
                async with httpx.AsyncClient(timeout=30.0) as client:
                    r = await client.post(
                        u, json={"model": model, "messages": msgs, "stream": False}, headers=headers
                    )
                    if r.is_success:
                        data = r.json()
                        content = ""
                        if is_openai:
                            choice = (data.get("choices") or [None])[0]
                            content = (choice or {}).get("message", {}).get("content", "")
                        else:
                            content = (data.get("message") or {}).get("content", "")
                        if content:
                            return {"role": "assistant", "content": content}
            except (httpx.HTTPError, OSError, KeyError):
                continue

        log.info("No LLM provider available for chat, falling back to rule-based planner")

    if body.execute:
        result = await execute_plan(body.message, params=body.params, execute=True)
    else:
        result = plan_goal(body.message)
    reply = result.get("message") or result.get("error") or "No plan generated."
    if result.get("executed") and result.get("results"):
        reply = f"{reply}\n\nExecuted {len(result['results'])} step(s)."
    return {"role": "assistant", "content": reply, "plan": result}


@router.post("/chat/stream")
async def api_chat_stream(body: ChatRequest):
    """Streaming chat — NDJSON SSE response from the first available LLM provider."""
    from fastapi.responses import StreamingResponse

    async def generate():
        if not body.system_prompt:
            yield _json.dumps({"type": "error", "content": "No system prompt configured."}) + "\n"
            return
        msgs: list[dict[str, str]] = [{"role": "system", "content": body.system_prompt}]
        for msg in body.history:
            msgs.append({"role": msg.role, "content": msg.content})
        msgs.append({"role": "user", "content": body.message})

        attempts = [
            (settings.ollama_base_url, settings.ollama_model, False),
            (settings.lmstudio_base_url, settings.openai_model, True),
        ]
        for base_url, model, is_openai in attempts:
            if not base_url or not model:
                continue
            try:
                u = f"{base_url.rstrip('/')}/{'v1/chat/completions' if is_openai else 'api/chat'}"
                async with httpx.AsyncClient(timeout=60.0) as client:
                    async with client.stream(
                        "POST", u, json={"model": model, "messages": msgs, "stream": True}
                    ) as resp:
                        if not resp.is_success:
                            continue
                        async for line in resp.aiter_lines():
                            if not line.strip():
                                continue
                            if is_openai:
                                if line.startswith("data: "):
                                    chunk = line[6:].strip()
                                    if chunk == "[DONE]":
                                        break
                                    try:
                                        data = _json.loads(chunk)
                                        delta = (data.get("choices") or [{}])[0].get("delta", {})
                                        content = delta.get("content", "")
                                        if content:
                                            yield (
                                                _json.dumps({"type": "delta", "content": content})
                                                + "\n"
                                            )
                                    except _json.JSONDecodeError:
                                        pass
                            else:
                                try:
                                    data = _json.loads(line)
                                    if data.get("done"):
                                        break
                                    content = (data.get("message") or {}).get("content", "")
                                    if content:
                                        yield (
                                            _json.dumps({"type": "delta", "content": content})
                                            + "\n"
                                        )
                                except _json.JSONDecodeError:
                                    pass
                        yield _json.dumps({"type": "done"}) + "\n"
                        return
            except Exception:
                continue
        yield _json.dumps({"type": "error", "content": "No LLM provider available."}) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")


@router.get("/tools")
async def api_tools() -> dict[str, Any]:
    """SOTA Tools Hub — libreoffice portmanteau surface."""
    return {
        "success": True,
        "tools": [
            {
                "name": "libreoffice",
                "kind": "portmanteau",
                "description": "General LibreOffice automation — Writer/Calc/Impress convert, merge, batch, PDF, watch",
                "operations": [
                    {
                        "name": "status",
                        "description": "soffice path, version, extension bridge health",
                    },
                    {"name": "help", "description": "Capability summary + REST routes"},
                    {
                        "name": "convert",
                        "description": "Headless single-file convert (.md → HTML → PDF, etc.)",
                    },
                    {
                        "name": "convert_batch",
                        "description": "Convert many files to one output format",
                    },
                    {
                        "name": "document_info",
                        "description": "Detect Writer/Calc/Impress and suggested export formats",
                    },
                    {
                        "name": "merge",
                        "description": "ODT template {{PLACEHOLDER}} merge → pdf/odt/docx",
                    },
                    {"name": "list_templates", "description": "Bundled + custom ODT templates"},
                    {"name": "batch_pack", "description": "Multiple .md paths → single PDF pack"},
                    {"name": "pdf_merge", "description": "Combine multiple PDFs (pypdf)"},
                    {
                        "name": "watch_start",
                        "description": "Poll folder and auto-convert new files",
                    },
                    {"name": "watch_stop", "description": "Stop folder watch"},
                    {"name": "watch_status", "description": "Active watch folders and last events"},
                    {"name": "reveal_output", "description": "Open output file in OS file manager"},
                    {
                        "name": "writer_session_status",
                        "description": "Live Writer bridge macro connected?",
                    },
                    {"name": "launch_writer", "description": "Open LibreOffice Writer GUI"},
                    {
                        "name": "live_write",
                        "description": "NL prompt → generate → typewriter in Writer",
                    },
                    {"name": "live_type", "description": "Type given text live with pacing"},
                    {"name": "run_macro", "description": "Run Basic UNO macro via .oxt bridge"},
                    {"name": "run_python_macro", "description": "Run Python UNO macro via bridge"},
                    {"name": "list_macros", "description": "List document Basic macro modules"},
                    {"name": "bridge_discover", "description": "List tools on extension MCP :8765"},
                    {
                        "name": "bridge_call",
                        "description": "Proxy call to extension (live Writer/Calc)",
                    },
                ],
            },
            {
                "name": "libreoffice_help",
                "kind": "atomic",
                "description": "Topic-based help for convert, merge, coworker, bridge, agentic",
                "operations": [],
            },
            {
                "name": "libreoffice_agentic_workflow",
                "kind": "agentic",
                "description": "Multi-step document goals via ctx.sample (SEP-1577)",
                "operations": [],
            },
            {
                "name": "show_libreoffice_status_card",
                "kind": "prefab",
                "description": "Prefab card — soffice + bridge health",
                "operations": [],
            },
            {
                "name": "show_templates_card",
                "kind": "prefab",
                "description": "Prefab card — bundled ODT template gallery",
                "operations": [],
            },
        ],
    }


@router.get("/help")
async def api_help() -> dict[str, Any]:
    ensure_builtin_templates()
    return {
        "success": True,
        "title": "LibreOffice MCP",
        "version": __version__,
        "ports": {"backend": 10981, "frontend": 10983, "extension_bridge": 8765},
        "host": {
            "soffice": "LibreOffice 26.2.3.2+ recommended",
            "env": ["LIBREOFFICE_MCP_SOFFICE_PATH", "LIBREOFFICE_MCP_EXTENSION_BRIDGE_URL"],
        },
        "coworker_flows": [
            "coworker_weekly_report_pdf → fleet-report.odt",
            "coworker_board_pack → fleet-board-pack.odt",
            "coworker_artifact_pack → fleet-artifact-pack.odt",
        ],
        "templates": [t["name"] for t in list_templates()],
    }


@router.get("/status")
async def api_status() -> dict[str, Any]:
    return {"success": True, "data": await health_summary()}


@router.get("/templates")
async def api_templates() -> dict[str, Any]:
    ensure_builtin_templates()
    templates = list_templates()
    return {"success": True, "templates": templates, "count": len(templates)}


@router.get("/jobs")
async def api_jobs() -> dict[str, Any]:
    jobs = list_jobs()
    return {"success": True, "jobs": jobs, "count": len(jobs)}


@router.get("/jobs/{job_id}")
async def api_job(job_id: str) -> dict[str, Any]:
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return {"success": True, "job": job}


@router.post("/convert")
async def api_convert(body: ConvertRequest) -> dict[str, Any]:
    src = Path(body.input_path)
    if not src.is_file():
        raise HTTPException(status_code=400, detail=f"Input not found: {src}")
    job = enqueue_convert(src, body.output_format)
    return {"success": True, "job": job, "message": "Convert job queued"}


@router.post("/merge")
async def api_merge(body: MergeRequest) -> dict[str, Any]:
    result = merge_and_convert(
        body.template,
        body.placeholders,
        body.output_format,
        output_stem=body.output_stem,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Merge failed"))
    return {"success": True, "data": result, "message": "Template merged"}


@router.post("/pack")
async def api_pack(body: PackRequest) -> dict[str, Any]:
    result = pack_markdown_files(
        [Path(p) for p in body.input_paths],
        title=body.title,
        output_stem=body.output_stem or "batch-pack",
        output_format=body.output_format,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Pack failed"))
    return {"success": True, "data": result, "message": f"Packed {result.get('count', 0)} files"}


@router.get("/output")
async def api_output() -> dict[str, Any]:
    out = settings.output_dir
    files: list[dict[str, Any]] = []
    if out.is_dir():
        for path in sorted(out.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)[:30]:
            if path.is_file():
                stat = path.stat()
                ext = path.suffix.lower()
                files.append(
                    {
                        "name": path.name,
                        "path": str(path),
                        "size_bytes": stat.st_size,
                        "modified": stat.st_mtime,
                        "previewable": ext in {".pdf", ".html", ".htm"},
                    }
                )
    return {"success": True, "output_dir": str(out), "files": files}


@router.get("/output/file/{filename}")
async def api_output_file(filename: str) -> FileResponse:
    path = _safe_output_file(filename)
    media_type, _ = mimetypes.guess_type(path.name)
    return FileResponse(
        path,
        media_type=media_type or "application/octet-stream",
        filename=path.name,
    )


@router.post("/output/reveal/{filename}")
async def api_output_reveal(filename: str) -> dict[str, Any]:
    path = _safe_output_file(filename)
    result = reveal_path(path)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Reveal failed"))
    return result


@router.post("/upload")
async def api_upload(file: Annotated[UploadFile, File()]) -> dict[str, Any]:
    """Upload a document for convert/merge (saved under ~/.libreoffice-mcp/uploads)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")
    safe_name = Path(file.filename).name
    if safe_name != file.filename or ".." in safe_name:
        raise HTTPException(status_code=400, detail="Invalid filename")

    settings.ensure_dirs()
    dest = settings.upload_dir / safe_name
    data = await file.read()
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail=f"Max upload {settings.max_upload_bytes} bytes")
    dest.write_bytes(data)

    info = document_info(dest)
    return {
        "success": True,
        "path": str(dest.resolve()),
        "name": safe_name,
        "size_bytes": len(data),
        "document": info,
    }


@router.get("/document/info")
async def api_document_info(
    path: str = Query(..., description="Absolute path to document"),
) -> dict[str, Any]:
    info = document_info(Path(path))
    if not info.get("success"):
        raise HTTPException(status_code=400, detail=str(info.get("error")))
    return {"success": True, "data": info}


@router.get("/formats")
async def api_formats(path: str | None = Query(default=None)) -> dict[str, Any]:
    from .formats import CALC_OUTPUT, IMPRESS_OUTPUT, WRITER_OUTPUT

    if path:
        p = Path(path)
        return {
            "success": True,
            "path": str(p),
            "suggested_formats": suggested_formats(p),
        }
    return {
        "success": True,
        "writer": WRITER_OUTPUT,
        "calc": CALC_OUTPUT,
        "impress": IMPRESS_OUTPUT,
    }


@router.post("/convert/batch")
async def api_convert_batch(body: BatchConvertRequest) -> dict[str, Any]:
    paths = [Path(p) for p in body.input_paths]
    missing = [str(p) for p in paths if not p.is_file()]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing files: {missing[:5]}")
    result = convert_batch(paths, body.output_format)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail="Batch convert produced no outputs")
    return {"success": True, "data": result}


@router.post("/pdf/merge")
async def api_pdf_merge(body: PdfMergeRequest) -> dict[str, Any]:
    result = merge_pdfs([Path(p) for p in body.input_paths], output_stem=body.output_stem)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "PDF merge failed"))
    return {"success": True, "data": result}


@router.get("/watch/status")
async def api_watch_status() -> dict[str, Any]:
    return {"success": True, "data": watch_status()}


@router.post("/watch/start")
async def api_watch_start(body: WatchRequest) -> dict[str, Any]:
    result = start_watch(
        body.watch_path, glob_pattern=body.glob_pattern, output_format=body.output_format
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Watch failed"))
    return result


@router.post("/watch/stop")
async def api_watch_stop() -> dict[str, Any]:
    return stop_watch()


@router.get("/tests/run")
async def api_tests_run(include_soffice: bool = Query(default=True)) -> dict[str, Any]:
    return run_self_tests(include_soffice=include_soffice)


@router.get("/output/index")
async def api_output_index() -> dict[str, Any]:
    files = list_indexed_outputs()
    return {"success": True, "output_dir": str(settings.output_dir), "files": files}
