"""Shared LibreOffice portmanteau operation dispatch (MCP + REST + agentic)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, cast, get_args

from .bridge import call_extension_tool, health_summary, probe_extension_bridge
from .config import settings
from .formats import document_info, suggested_formats
from .headless import convert_batch, convert_file
from .jobs import enqueue_convert
from .live_session import writer_session_status as get_writer_session_status
from .live_write import live_type_text, live_write
from .macro_ops import (
    MacroLanguage,
    MacroLocation,
    build_macro_uri,
    list_macros_action,
    macro_action_payload,
)
from .pack import pack_markdown_files
from .pdf_ops import merge_pdfs
from .reveal import reveal_path
from .storage import index_output
from .templates import ensure_builtin_templates, list_templates, merge_and_convert
from .watch_folder import start_watch, stop_watch, watch_status
from .writer_runtime import execute_writer_action, launch_writer_gui

LibreOfficeOp = Literal[
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


async def execute_libreoffice_operation(
    operation: str,
    *,
    input_path: str | None = None,
    output_format: str = "pdf",
    template: str | None = None,
    placeholders: dict[str, str] | None = None,
    output_stem: str | None = None,
    input_paths: list[str] | None = None,
    pack_title: str | None = None,
    bridge_tool: str | None = None,
    bridge_arguments: dict[str, Any] | None = None,
    bridge_url: str | None = None,
    queue_job: bool = False,
    watch_path: str | None = None,
    watch_glob: str = "*.*",
    prompt: str | None = None,
    live_text: str | None = None,
    prefer_session: bool = True,
    typewriter_wpm: float | None = None,
    max_words: int | None = None,
    headless_fallback: bool = True,
    macro_uri: str | None = None,
    macro_name: str | None = None,
    macro_language: str = "Basic",
    macro_location: str = "application",
    macro_library: str | None = None,
    macro_module: str | None = None,
    macro_args: list[Any] | None = None,
) -> dict[str, Any]:
    if operation == "status":
        return {"success": True, "data": await health_summary()}

    if operation == "help":
        ensure_builtin_templates()
        return {
            "success": True,
            "message": "LibreOffice MCP — Writer, Calc, Impress headless automation + extension bridge",
            "operations": list(get_args(LibreOfficeOp)),
            "writer_formats": ["pdf", "docx", "odt", "html", "txt", "rtf"],
            "calc_formats": ["pdf", "xlsx", "ods", "csv", "html"],
            "impress_formats": ["pdf", "pptx", "odp", "html"],
            "coworker_flows": [
                "coworker_weekly_report_pdf → fleet-report.odt",
                "coworker_board_pack → fleet-board-pack.odt",
                "coworker_artifact_pack → fleet-artifact-pack.odt (merge)",
            ],
            "templates": [t["name"] for t in list_templates()],
            "fleet_ports": {"backend": 10981, "frontend": 10983},
        }

    if operation == "list_templates":
        ensure_builtin_templates()
        return {"success": True, "data": {"templates": list_templates()}}

    if operation == "document_info":
        if not input_path:
            return {"success": False, "error": "input_path required for document_info"}
        info = document_info(Path(input_path))
        return {"success": info.get("success", False), "data": info}

    if operation == "merge":
        if not template:
            return {"success": False, "error": "template required for merge"}
        result = merge_and_convert(
            template,
            placeholders or {},
            output_format,
            output_stem=output_stem,
        )
        return {"success": result.get("success", False), "data": result}

    if operation == "batch_pack":
        if not input_paths:
            return {"success": False, "error": "input_paths required for batch_pack"}
        result = pack_markdown_files(
            [Path(p) for p in input_paths],
            title=pack_title or "Document Pack",
            output_stem=output_stem or "batch-pack",
            output_format=output_format,
        )
        if result.get("success") and result.get("output"):
            index_output(Path(result["output"]), fmt=output_format)
        return {"success": result.get("success", False), "data": result}

    if operation == "pdf_merge":
        if not input_paths:
            return {"success": False, "error": "input_paths required for pdf_merge (PDF files)"}
        result = merge_pdfs(
            [Path(p) for p in input_paths],
            output_stem=output_stem or "merged",
        )
        if result.get("success") and result.get("output"):
            index_output(Path(result["output"]), fmt="pdf")
        return {"success": result.get("success", False), "data": result}

    if operation == "convert_batch":
        if not input_paths:
            return {"success": False, "error": "input_paths required for convert_batch"}
        result = convert_batch([Path(p) for p in input_paths], output_format)
        for item in result.get("results", []):
            if item.get("success") and item.get("output"):
                index_output(Path(item["output"]), fmt=output_format)
        return {"success": result.get("success", False), "data": result}

    if operation == "convert":
        if not input_path:
            return {"success": False, "error": "input_path required for convert"}
        src = Path(input_path)
        if queue_job:
            job = enqueue_convert(src, output_format)
            return {"success": True, "data": {"job": job}, "message": "Convert job queued"}
        result = convert_file(src, output_format)
        if result.get("success") and result.get("output"):
            index_output(Path(result["output"]), fmt=output_format, job_id=None)
        if not result.get("success") and not result.get("suggested_formats"):
            result["suggested_formats"] = suggested_formats(src)
        return {"success": result.get("success", False), "data": result}

    if operation == "watch_start":
        if not watch_path and not input_path:
            return {"success": False, "error": "watch_path or input_path required for watch_start"}
        data = start_watch(
            watch_path or input_path or "",
            glob_pattern=watch_glob,
            output_format=output_format,
        )
        return data

    if operation == "watch_stop":
        return stop_watch()

    if operation == "watch_status":
        return {"success": True, "data": watch_status()}

    if operation == "writer_session_status":
        return {"success": True, "data": get_writer_session_status()}

    if operation == "launch_writer":
        return launch_writer_gui()

    if operation == "live_write":
        if not prompt:
            return {"success": False, "error": "prompt required for live_write"}
        wpm = typewriter_wpm if typewriter_wpm is not None else settings.live_typewriter_wpm
        words = max_words if max_words is not None else settings.live_max_words
        result = await live_write(
            prompt,
            wpm=wpm,
            max_words=words,
            prefer_session=prefer_session,
            headless_fallback=headless_fallback,
        )
        return {"success": result.get("success", False), "data": result}

    if operation == "live_type":
        if not live_text and not prompt:
            return {"success": False, "error": "live_text or prompt required for live_type"}
        wpm = typewriter_wpm if typewriter_wpm is not None else settings.live_typewriter_wpm
        result = await live_type_text(
            live_text or prompt or "",
            wpm=wpm,
            prefer_session=prefer_session,
            headless_fallback=headless_fallback,
        )
        return {"success": result.get("success", False), "data": result}

    if operation == "list_macros":
        result = await execute_writer_action(
            list_macros_action(),
            prefer_session=True,
            headless_fallback=False,
            timeout=20.0,
        )
        return {"success": result.get("success", False), "data": result}

    if operation in ("run_macro", "run_python_macro"):
        if not macro_uri and not macro_name:
            return {"success": False, "error": "macro_uri or macro_name required"}
        lang: MacroLanguage = "Python" if operation == "run_python_macro" else cast(
            MacroLanguage, macro_language or "Basic"
        )
        loc = cast(MacroLocation, macro_location or "application")
        try:
            action = macro_action_payload(
                macro_uri=macro_uri,
                macro_name=macro_name,
                language=lang,
                location=loc,
                library=macro_library,
                module=macro_module,
                args=macro_args,
            )
        except ValueError as exc:
            return {"success": False, "error": str(exc)}
        result = await execute_writer_action(
            action,
            prefer_session=prefer_session,
            headless_fallback=False,
            timeout=60.0,
        )
        if macro_uri is None and macro_name:
            result["macro_uri"] = build_macro_uri(
                macro_name,
                language=lang,
                location=loc,
                library=macro_library,
                module=macro_module,
            )
        return {"success": result.get("success", False), "data": result}

    if operation == "reveal_output":
        target = input_path or output_stem
        if not target:
            return {"success": False, "error": "input_path required for reveal_output"}
        p = Path(target)
        if not p.is_absolute():
            p = settings.output_dir / target
        return reveal_path(p)

    if operation == "bridge_discover":
        data = await probe_extension_bridge(bridge_url)
        return {"success": True, "data": data}

    if operation == "bridge_call":
        if not bridge_tool:
            return {"success": False, "error": "bridge_tool required for bridge_call"}
        data = await call_extension_tool(bridge_tool, bridge_arguments, url=bridge_url)
        return {"success": data.get("success", False), "data": data}

    return {"success": False, "error": f"Unknown operation: {operation}"}
