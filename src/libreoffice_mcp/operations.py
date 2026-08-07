"""Shared LibreOffice portmanteau operation dispatch (MCP + REST + agentic)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, get_args

from .bridge import call_extension_tool, health_summary, probe_extension_bridge
from .config import settings
from .formats import document_info, suggested_formats
from .headless import convert_batch, convert_file
from .jobs import enqueue_convert
from .pack import pack_markdown_files
from .pdf_ops import merge_pdfs
from .reveal import reveal_path
from .spreadsheet_read import read_spreadsheet_data
from .storage import index_output
from .templates import ensure_builtin_templates, list_templates, merge_and_convert
from .watch_folder import start_watch, stop_watch, watch_status

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
    "read_spreadsheet",
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
            "writer_portmanteau": "libreoffice_writer(operation=…)",
            "calc_portmanteau": "libreoffice_calc(operation=…)",
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
        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "next_steps": result.get("next_steps", []),
            "data": result,
        }

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
        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "next_steps": result.get("next_steps", []),
            "data": result,
        }

    if operation == "pdf_merge":
        if not input_paths:
            return {"success": False, "error": "input_paths required for pdf_merge (PDF files)"}
        result = merge_pdfs(
            [Path(p) for p in input_paths],
            output_stem=output_stem or "merged",
        )
        if result.get("success") and result.get("output"):
            index_output(Path(result["output"]), fmt="pdf")
        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "next_steps": result.get("next_steps", []),
            "data": result,
        }

    if operation == "convert_batch":
        if not input_paths:
            return {"success": False, "error": "input_paths required for convert_batch"}
        result = convert_batch([Path(p) for p in input_paths], output_format)
        for item in result.get("results", []):
            if item.get("success") and item.get("output"):
                index_output(Path(item["output"]), fmt=output_format)
        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "next_steps": result.get("next_steps", []),
            "data": result,
        }

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
        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "next_steps": result.get("next_steps", []),
            "data": result,
        }

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

    if operation in (
        "writer_session_status",
        "launch_writer",
        "live_write",
        "live_type",
        "list_macros",
        "run_macro",
        "run_python_macro",
    ):
        from .writer_ops import execute_libreoffice_writer_operation

        op_map = {
            "writer_session_status": "status",
            "launch_writer": "launch_writer",
            "live_write": "live_write",
            "live_type": "live_type",
            "list_macros": "list_macros",
            "run_macro": "run_macro",
            "run_python_macro": "run_python_macro",
        }
        return await execute_libreoffice_writer_operation(
            op_map[operation],
            prompt=prompt,
            live_text=live_text,
            prefer_session=prefer_session,
            headless_fallback=headless_fallback,
            typewriter_wpm=typewriter_wpm,
            max_words=max_words,
            macro_uri=macro_uri,
            macro_name=macro_name,
            macro_language=macro_language,
            macro_location=macro_location,
            macro_library=macro_library,
            macro_module=macro_module,
            macro_args=macro_args,
        )

    if operation == "read_spreadsheet":
        if not input_path:
            return {"success": False, "error": "input_path required for read_spreadsheet"}
        data = read_spreadsheet_data(Path(input_path))
        return {"success": data.get("success", False), "data": data}

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
