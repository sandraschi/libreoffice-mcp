"""LibreOffice webapp action catalog - simple ops and multi-step coworker workflows."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .bridge import call_extension_tool, health_summary, probe_extension_bridge
from .formats import document_info
from .headless import convert_batch, convert_file
from .jobs import enqueue_convert
from .live_write import live_write
from .operations import execute_libreoffice_operation
from .pack import pack_markdown_files
from .pdf_ops import merge_pdfs
from .templates import ensure_builtin_templates, list_templates, merge_and_convert
from .watch_folder import start_watch

SIMPLE_ACTIONS: list[dict[str, Any]] = [
    {
        "id": "status",
        "label": "System status",
        "description": "soffice path, version, and extension bridge health",
        "operation": "status",
        "params": [],
    },
    {
        "id": "live_write",
        "label": "Live write (typewriter)",
        "description": "Generate prose and type it in live Writer - watch the agent write",
        "operation": "live_write",
        "params": [
            {
                "name": "prompt",
                "type": "text",
                "required": True,
                "label": "What to write",
                "default": "Write a short story about butterflies",
            },
            {
                "name": "typewriter_wpm",
                "type": "number",
                "required": False,
                "default": 180,
                "label": "Typing speed (WPM)",
            },
            {
                "name": "prefer_session",
                "type": "boolean",
                "required": False,
                "default": True,
                "label": "Prefer live Writer bridge",
            },
        ],
    },
    {
        "id": "writer_session_status",
        "label": "Writer bridge status",
        "description": "Is the live Writer macro bridge connected?",
        "operation": "writer_session_status",
        "params": [],
    },
    {
        "id": "bridge_discover",
        "label": "Extension bridge",
        "description": "List live Writer/Calc tools on :8765 MCP bridge",
        "operation": "bridge_discover",
        "params": [],
    },
    {
        "id": "list_templates",
        "label": "List templates",
        "description": "Bundled fleet ODT templates and placeholders",
        "operation": "list_templates",
        "params": [],
    },
    {
        "id": "convert",
        "label": "Convert file",
        "description": "Headless convert - markdown renders to HTML before PDF",
        "operation": "convert",
        "params": [
            {"name": "input_path", "type": "path", "required": True, "label": "Source file"},
            {
                "name": "output_format",
                "type": "select",
                "required": False,
                "default": "pdf",
                "options": ["pdf", "odt", "docx", "html", "xlsx", "csv", "pptx", "ods", "odp"],
            },
            {
                "name": "queue_job",
                "type": "boolean",
                "required": False,
                "default": True,
                "label": "Track as job",
            },
        ],
    },
    {
        "id": "document_info",
        "label": "Document info",
        "description": "Detect Writer/Calc/Impress family and suggested export formats",
        "operation": "document_info",
        "params": [
            {"name": "input_path", "type": "path", "required": True, "label": "Document path"},
        ],
    },
    {
        "id": "pdf_merge",
        "label": "Merge PDFs",
        "description": "Combine multiple PDF files into one",
        "operation": "pdf_merge",
        "params": [
            {
                "name": "input_paths",
                "type": "paths",
                "required": True,
                "label": "PDF paths (one per line)",
            },
            {"name": "output_stem", "type": "text", "required": False, "default": "merged"},
        ],
    },
    {
        "id": "quick_merge",
        "label": "Quick template merge",
        "description": "Merge one ODT template to PDF without the full gallery",
        "operation": "merge",
        "params": [
            {
                "name": "template",
                "type": "select",
                "required": True,
                "options_from": "templates",
            },
            {"name": "output_stem", "type": "text", "required": False},
            {
                "name": "output_format",
                "type": "select",
                "required": False,
                "default": "pdf",
                "options": ["pdf", "odt"],
            },
        ],
        "dynamic_placeholders": True,
    },
]

COMPLEX_WORKFLOWS: list[dict[str, Any]] = [
    {
        "id": "coworker_weekly_report_pdf",
        "label": "Weekly fleet report",
        "description": "Merge fleet-report.odt → PDF for Fritz coworker_weekly_report_pdf",
        "template": "fleet-report.odt",
        "coworker_flow": "coworker_weekly_report_pdf",
        "output_stem_default": "fleet-weekly-report",
        "placeholders": [
            {"key": "TITLE", "label": "Report title", "default": "Fleet Weekly Report"},
            {"key": "DATE", "label": "Report date", "default_from": "today"},
            {"key": "SUMMARY", "label": "Executive summary", "multiline": True},
            {"key": "BODY", "label": "Report body (markdown ok)", "multiline": True},
        ],
    },
    {
        "id": "coworker_board_pack",
        "label": "Board pack",
        "description": "Merge fleet-board-pack.odt → PDF for coworker_board_pack",
        "template": "fleet-board-pack.odt",
        "coworker_flow": "coworker_board_pack",
        "output_stem_default": "fleet-board-pack",
        "placeholders": [
            {"key": "TITLE", "label": "Pack title", "default": "Fleet Board Pack"},
            {"key": "DATE", "label": "Meeting date", "default_from": "today"},
            {"key": "KPI_TABLE", "label": "KPI table (text/markdown)", "multiline": True},
            {"key": "NARRATIVE", "label": "Narrative", "multiline": True},
            {"key": "ACTION_ITEMS", "label": "Action items", "multiline": True},
        ],
    },
    {
        "id": "coworker_artifact_pack",
        "label": "Artifact pack (merge)",
        "description": "Single merged PDF from fleet-artifact-pack.odt placeholders",
        "template": "fleet-artifact-pack.odt",
        "coworker_flow": "coworker_artifact_pack",
        "output_stem_default": "fleet-artifact-pack",
        "placeholders": [
            {"key": "TITLE", "label": "Pack title", "default": "Fleet Artifact Pack"},
            {"key": "DATE", "label": "Pack date", "default_from": "today"},
            {"key": "FILE_COUNT", "label": "File count", "default": "0"},
            {"key": "BODY", "label": "Combined body", "multiline": True},
        ],
    },
    {
        "id": "batch_markdown_pack",
        "label": "Batch markdown pack",
        "description": "Multiple .md paths → styled PDF via pack engine",
        "operation": "batch_pack",
        "output_stem_default": "batch-pack",
        "params": [
            {
                "name": "input_paths",
                "type": "paths",
                "required": True,
                "label": "Markdown paths (one per line)",
            },
            {"name": "title", "type": "text", "required": False, "default": "Document Pack"},
            {"name": "output_stem", "type": "text", "required": False},
            {
                "name": "output_format",
                "type": "select",
                "required": False,
                "default": "pdf",
                "options": ["pdf"],
            },
        ],
    },
    {
        "id": "pdf_merge",
        "label": "Merge PDF files",
        "description": "Combine multiple PDFs into one output file",
        "operation": "pdf_merge",
        "output_stem_default": "merged",
        "params": [
            {"name": "input_paths", "type": "paths", "required": True, "label": "PDF paths"},
            {"name": "output_stem", "type": "text", "required": False},
        ],
    },
    {
        "id": "folder_watch",
        "label": "Watch folder",
        "description": "Auto-convert new/changed files in a directory",
        "operation": "watch_start",
        "params": [
            {"name": "watch_path", "type": "path", "required": True, "label": "Folder to watch"},
            {"name": "glob_pattern", "type": "text", "required": False, "default": "*.*"},
            {
                "name": "output_format",
                "type": "select",
                "required": False,
                "default": "pdf",
                "options": ["pdf", "docx", "odt", "xlsx", "pptx", "html"],
            },
        ],
    },
    {
        "id": "convert_batch",
        "label": "Batch convert",
        "description": "Convert many files to the same format (Writer, Calc, Impress)",
        "operation": "convert_batch",
        "params": [
            {"name": "input_paths", "type": "paths", "required": True, "label": "File paths"},
            {
                "name": "output_format",
                "type": "select",
                "required": False,
                "default": "pdf",
                "options": ["pdf", "docx", "odt", "xlsx", "csv", "pptx", "html"],
            },
        ],
    },
    {
        "id": "bridge_call",
        "label": "Extension bridge call",
        "description": "Proxy a tool call to live LibreOffice via WriterAgent / mcp-libre",
        "operation": "bridge_call",
        "params": [
            {"name": "bridge_tool", "type": "text", "required": True, "label": "Tool name"},
            {
                "name": "bridge_arguments",
                "type": "json",
                "required": False,
                "default": "{}",
                "label": "Arguments (JSON)",
            },
        ],
    },
]


def _today() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def catalog() -> dict[str, Any]:
    ensure_builtin_templates()
    templates = list_templates()
    return {
        "simple_actions": SIMPLE_ACTIONS,
        "workflows": COMPLEX_WORKFLOWS,
        "templates": templates,
        "defaults": {"today": _today()},
    }


async def run_simple_action(action_id: str, params: dict[str, Any]) -> dict[str, Any]:
    action = next((a for a in SIMPLE_ACTIONS if a["id"] == action_id), None)
    if not action:
        return {"success": False, "error": f"Unknown action: {action_id}"}

    op = action["operation"]

    if op == "writer_session_status":
        data = await execute_libreoffice_operation("writer_session_status")
        return {"success": True, "action_id": action_id, "data": data.get("data")}

    if op == "live_write":
        prompt = str(params.get("prompt") or "").strip()
        if not prompt:
            return {"success": False, "error": "prompt required"}
        result = await live_write(
            prompt,
            wpm=float(params.get("typewriter_wpm") or 180),
            prefer_session=bool(params.get("prefer_session", True)),
            headless_fallback=bool(params.get("headless_fallback", True)),
        )
        return {
            "success": result.get("success", False),
            "action_id": action_id,
            "data": result,
            "message": "Live write finished" if result.get("success") else result.get("error"),
        }

    if op == "status":
        data = await health_summary()
        return {"success": True, "action_id": action_id, "data": data}

    if op == "bridge_discover":
        data = await probe_extension_bridge()
        return {"success": True, "action_id": action_id, "data": data}

    if op == "list_templates":
        ensure_builtin_templates()
        return {"success": True, "action_id": action_id, "data": {"templates": list_templates()}}

    if op == "convert":
        input_path = params.get("input_path")
        if not input_path:
            return {"success": False, "error": "input_path required"}
        src = Path(str(input_path))
        if not src.is_file():
            return {"success": False, "error": f"Input not found: {src}"}
        fmt = str(params.get("output_format") or "pdf")
        if params.get("queue_job", True):
            job = enqueue_convert(src, fmt)
            return {
                "success": True,
                "action_id": action_id,
                "message": "Convert job queued",
                "data": {"job": job},
            }
        result = convert_file(src, fmt)
        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "next_steps": result.get("next_steps", []),
            "action_id": action_id,
            "data": result,
        }

    if op == "merge":
        template = params.get("template")
        if not template:
            return {"success": False, "error": "template required"}
        placeholders = params.get("placeholders") or {}
        if not isinstance(placeholders, dict):
            return {"success": False, "error": "placeholders must be an object"}
        fmt = str(params.get("output_format") or "pdf")
        stem = params.get("output_stem")
        result = merge_and_convert(
            str(template),
            {str(k): str(v) for k, v in placeholders.items()},
            fmt,
            output_stem=str(stem) if stem else None,
        )
        if not result.get("success"):
            return {
                "success": False,
                "action_id": action_id,
                "error": result.get("error", "Merge failed"),
            }
        return {
            "success": True,
            "action_id": action_id,
            "data": result,
            "message": "Template merged",
        }

    if op == "document_info":
        input_path = params.get("input_path")
        if not input_path:
            return {"success": False, "error": "input_path required"}
        info = document_info(Path(str(input_path)))
        return {
            "success": info.get("success", False),
            "message": info.get("message", ""),
            "next_steps": info.get("next_steps", []),
            "action_id": action_id,
            "data": info,
        }

    if op == "pdf_merge":
        raw = params.get("input_paths") or []
        paths = (
            [p.strip() for p in raw.splitlines() if p.strip()]
            if isinstance(raw, str)
            else [str(p).strip() for p in raw if str(p).strip()]
        )
        result = merge_pdfs(
            [Path(p) for p in paths], output_stem=str(params.get("output_stem") or "merged")
        )
        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "next_steps": result.get("next_steps", []),
            "action_id": action_id,
            "data": result,
        }

    delegated = await execute_libreoffice_operation(
        op,
        input_path=params.get("input_path"),
        output_format=str(params.get("output_format") or "pdf"),
        input_paths=params.get("input_paths"),
        watch_path=params.get("watch_path"),
        watch_glob=str(params.get("glob_pattern") or "*.*"),
    )
    if delegated.get("success") is not False or op in {"watch_start", "watch_stop", "watch_status"}:
        return {"success": delegated.get("success", True), "action_id": action_id, **delegated}

    return {"success": False, "error": f"Unhandled action operation: {op}"}


async def run_workflow(workflow_id: str, params: dict[str, Any]) -> dict[str, Any]:
    wf = next((w for w in COMPLEX_WORKFLOWS if w["id"] == workflow_id), None)
    if not wf:
        return {"success": False, "error": f"Unknown workflow: {workflow_id}"}

    if wf.get("template"):
        placeholders = params.get("placeholders") or {}
        if not isinstance(placeholders, dict):
            return {"success": False, "error": "placeholders must be an object"}
        fmt = str(params.get("output_format") or "pdf")
        stem = params.get("output_stem") or wf.get("output_stem_default")
        result = merge_and_convert(
            wf["template"],
            {str(k): str(v) for k, v in placeholders.items()},
            fmt,
            output_stem=str(stem) if stem else None,
        )
        if not result.get("success"):
            return {
                "success": False,
                "workflow_id": workflow_id,
                "error": result.get("error", "Merge failed"),
            }
        return {
            "success": True,
            "workflow_id": workflow_id,
            "coworker_flow": wf.get("coworker_flow"),
            "data": result,
            "message": f"Workflow {workflow_id} completed",
        }

    op = wf.get("operation")

    if op == "batch_pack":
        raw_paths = params.get("input_paths") or []
        if isinstance(raw_paths, str):
            paths = [p.strip() for p in raw_paths.splitlines() if p.strip()]
        else:
            paths = [str(p).strip() for p in raw_paths if str(p).strip()]
        if not paths:
            return {"success": False, "error": "input_paths required"}
        title = str(params.get("title") or "Document Pack")
        stem = str(params.get("output_stem") or wf.get("output_stem_default") or "batch-pack")
        fmt = str(params.get("output_format") or "pdf")
        result = pack_markdown_files(
            [Path(p) for p in paths],
            title=title,
            output_stem=stem,
            output_format=fmt,
        )
        if not result.get("success"):
            return {
                "success": False,
                "workflow_id": workflow_id,
                "error": result.get("error", "Pack failed"),
            }
        return {
            "success": True,
            "workflow_id": workflow_id,
            "data": result,
            "message": f"Packed {result.get('count', len(paths))} files",
        }

    if op == "bridge_call":
        tool = params.get("bridge_tool")
        if not tool:
            return {"success": False, "error": "bridge_tool required"}
        args = params.get("bridge_arguments") or {}
        if isinstance(args, str):
            import json

            try:
                args = json.loads(args) if args.strip() else {}
            except json.JSONDecodeError as exc:
                return {"success": False, "error": f"Invalid bridge_arguments JSON: {exc}"}
        data = await call_extension_tool(str(tool), args if isinstance(args, dict) else {})
        return {
            "success": data.get("success", False),
            "workflow_id": workflow_id,
            "data": data,
        }

    if op == "pdf_merge":
        raw_paths = params.get("input_paths") or []
        paths = (
            [p.strip() for p in raw_paths.splitlines() if p.strip()]
            if isinstance(raw_paths, str)
            else [str(p).strip() for p in raw_paths if str(p).strip()]
        )
        stem = str(params.get("output_stem") or wf.get("output_stem_default") or "merged")
        result = merge_pdfs([Path(p) for p in paths], output_stem=stem)
        if not result.get("success"):
            return {
                "success": False,
                "workflow_id": workflow_id,
                "error": result.get("error", "Merge failed"),
            }
        return {"success": True, "workflow_id": workflow_id, "data": result}

    if op == "convert_batch":
        raw_paths = params.get("input_paths") or []
        paths = (
            [p.strip() for p in raw_paths.splitlines() if p.strip()]
            if isinstance(raw_paths, str)
            else [str(p).strip() for p in raw_paths if str(p).strip()]
        )
        fmt = str(params.get("output_format") or "pdf")
        result = convert_batch([Path(p) for p in paths], fmt)
        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "next_steps": result.get("next_steps", []),
            "workflow_id": workflow_id,
            "data": result,
        }

    if op == "watch_start":
        watch_path = params.get("watch_path")
        if not watch_path:
            return {"success": False, "error": "watch_path required"}
        result = start_watch(
            str(watch_path),
            glob_pattern=str(params.get("glob_pattern") or "*.*"),
            output_format=str(params.get("output_format") or "pdf"),
        )
        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "next_steps": result.get("next_steps", []),
            "workflow_id": workflow_id,
            "data": result,
        }

    return {"success": False, "error": f"Unhandled workflow: {workflow_id}"}
