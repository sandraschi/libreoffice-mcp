"""LibreOffice MCP - FastMCP 3.3 server (headless + extension bridge + REST API)."""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import FastMCP
from fastmcp.server.providers.skills import SkillsDirectoryProvider
from pydantic import Field

from . import __version__
from .api import router as api_router
from .bridge import probe_extension_bridge
from .config import settings
from .headless import find_soffice
from .mcp_agentic import libreoffice_agentic_workflow
from .operations import LibreOfficeOp, execute_libreoffice_operation
from .prefab_tools import register_prefab_tools
from .sampling import LoSamplingHandler
from .templates import ensure_builtin_templates

_USE_CLIENT_SAMPLING = os.getenv("LIBREOFFICE_MCP_SAMPLING_USE_CLIENT_LLM", "").lower() in (
    "1",
    "true",
    "yes",
)

SKILLS_ROOT = Path(__file__).resolve().parent / "skills"
sampling_handler = LoSamplingHandler()

_MCP_INSTRUCTIONS = """You are LibreOffice MCP (FastMCP 3.3): headless document automation for the fleet.

CORE: Portmanteau `libreoffice(operation=...)` - convert, merge, batch_pack, status, bridge.
AGENTIC: `libreoffice_agentic_workflow(goal, ctx)` for multi-step tasks via sampling (SEP-1577).
PREFABS: `show_libreoffice_status_card`, `show_templates_card` for in-chat rich UI.
SKILLS: skill://*/SKILL.md - libreoffice-expert, coworker-pdf.
COWORKER: fleet-report.odt, fleet-board-pack.odt, fleet-artifact-pack.odt → PDF for Fritz flows.

Requires LibreOffice soffice on the host. Extension bridge optional on :8765/mcp."""

mcp = FastMCP(
    name="libreoffice-mcp",
    version=__version__,
    instructions=_MCP_INSTRUCTIONS,
    sampling_handler=sampling_handler,
    sampling_handler_behavior="fallback" if _USE_CLIENT_SAMPLING else "always",
)

if SKILLS_ROOT.is_dir():
    mcp.add_provider(SkillsDirectoryProvider(roots=SKILLS_ROOT, reload=False))


@mcp.tool(version="0.2.0", annotations={"readOnlyHint": False, "destructiveHint": False})
async def libreoffice(
    operation: Annotated[LibreOfficeOp, Field(description="Operation to run")],
    input_path: Annotated[str | None, Field(description="Source file for convert")] = None,
    output_format: Annotated[
        str, Field(description="Target format: pdf, docx, odt, html, xlsx, csv")
    ] = "pdf",
    template: Annotated[str | None, Field(description="ODT template name/path for merge")] = None,
    placeholders: Annotated[
        dict[str, str] | None, Field(description="{{KEY}} values for merge")
    ] = None,
    output_stem: Annotated[str | None, Field(description="Merged output filename stem")] = None,
    input_paths: Annotated[
        list[str] | None, Field(description="Markdown paths for batch_pack")
    ] = None,
    pack_title: Annotated[
        str | None, Field(description="Title for batch_pack combined document")
    ] = None,
    bridge_tool: Annotated[
        str | None, Field(description="Extension MCP tool name for bridge_call")
    ] = None,
    bridge_arguments: Annotated[
        dict[str, Any] | None, Field(description="Arguments for bridge_call")
    ] = None,
    bridge_url: Annotated[
        str | None, Field(description="Override extension MCP URL (default :8765/mcp)")
    ] = None,
    queue_job: Annotated[
        bool, Field(description="When true, convert runs as tracked job (REST/webapp)")
    ] = False,
    watch_path: Annotated[str | None, Field(description="Folder path for watch_start")] = None,
    watch_glob: Annotated[str, Field(description="Glob for watch_start (default *.*)")] = "*.*",
    prompt: Annotated[
        str | None, Field(description="Natural language prompt for live_write")
    ] = None,
    live_text: Annotated[str | None, Field(description="Text to type for live_type")] = None,
    prefer_session: Annotated[
        bool, Field(description="Prefer live Writer bridge over headless fallback")
    ] = True,
    typewriter_wpm: Annotated[
        float | None, Field(description="Typewriter speed (words per minute)")
    ] = None,
    max_words: Annotated[
        int | None, Field(description="Max words for live_write generation")
    ] = None,
    headless_fallback: Annotated[
        bool, Field(description="When live bridge offline, write ODT and open Writer")
    ] = True,
    macro_uri: Annotated[str | None, Field(description="Full vnd.sun.star.script URI")] = None,
    macro_name: Annotated[
        str | None, Field(description="Macro path e.g. Standard.Module1.MyMacro")
    ] = None,
    macro_language: Annotated[str, Field(description="Basic or Python")] = "Basic",
    macro_location: Annotated[str, Field(description="application or document")] = "application",
    macro_library: Annotated[str | None, Field(description="Basic library name")] = None,
    macro_module: Annotated[str | None, Field(description="Basic module name")] = None,
    macro_args: Annotated[list[Any] | None, Field(description="Macro invoke arguments")] = None,
) -> dict[str, Any]:
    """Portmanteau LibreOffice automation - headless + live Writer bridge + UNO macros.

    Install extension: dist/libreoffice-mcp-bridge.oxt (auto-starts on LO launch).

    ## Operations
    - status, convert, merge, batch_pack, pdf_merge, watch_*, live_write, live_type
    - run_macro, run_python_macro, list_macros (via .oxt bridge)
    - bridge_discover, bridge_call, help

    ## Return Format
    Returns a dict with `success` (bool), `data` (operation payload) on success,
    or `error` (message) on failure. Convert ops add `message` (e.g. job queued).

    ## Examples
    - `libreoffice(operation="status")` - soffice path + bridge health
    - `libreoffice(operation="convert", input_path="C:/docs/report.md",
      output_format="pdf")` - headless convert to PDF
    - `libreoffice(operation="merge", template="fleet-report.odt",
      placeholders={"TITLE": "Weekly"})` - ODT template merge
    """
    return await execute_libreoffice_operation(
        operation,
        input_path=input_path,
        output_format=output_format,
        template=template,
        placeholders=placeholders,
        output_stem=output_stem,
        input_paths=input_paths,
        pack_title=pack_title,
        bridge_tool=bridge_tool,
        bridge_arguments=bridge_arguments,
        bridge_url=bridge_url,
        queue_job=queue_job,
        watch_path=watch_path,
        watch_glob=watch_glob,
        prompt=prompt,
        live_text=live_text,
        prefer_session=prefer_session,
        typewriter_wpm=typewriter_wpm,
        max_words=max_words,
        headless_fallback=headless_fallback,
        macro_uri=macro_uri,
        macro_name=macro_name,
        macro_language=macro_language,
        macro_location=macro_location,
        macro_library=macro_library,
        macro_module=macro_module,
        macro_args=macro_args,
    )


@mcp.tool(version="0.3.0", annotations={"readOnlyHint": False, "destructiveHint": False})
async def libreoffice_writer(
    operation: Annotated[
        str, Field(description="Writer live op: status, live_write, live_type, …")
    ],
    prompt: Annotated[str | None, Field(description="Prompt for live_write")] = None,
    live_text: Annotated[str | None, Field(description="Text for live_type / insert_text")] = None,
    text: Annotated[str | None, Field(description="insert_text body")] = None,
    prefer_session: Annotated[bool, Field(description="Use live .oxt bridge")] = True,
    headless_fallback: Annotated[bool, Field(description="Fallback when bridge offline")] = True,
    typewriter_wpm: Annotated[float | None, Field(description="WPM for typewriter")] = None,
    max_words: Annotated[int | None, Field(description="Max words for live_write")] = None,
    macro_uri: Annotated[str | None, Field(description="UNO macro URI")] = None,
    macro_name: Annotated[str | None, Field(description="Macro name")] = None,
    macro_language: Annotated[str, Field(description="Basic or Python")] = "Basic",
    macro_location: Annotated[str, Field(description="application or document")] = "application",
    macro_library: Annotated[str | None, Field(description="Basic library")] = None,
    macro_module: Annotated[str | None, Field(description="Basic module")] = None,
    macro_args: Annotated[list[Any] | None, Field(description="Macro args")] = None,
    document_path: Annotated[str | None, Field(description="Open existing document")] = None,
) -> dict[str, Any]:
    """Live Writer portmanteau - typewriter, macros (libreoffice-mcp-bridge.oxt).

    ## Return Format
    Returns a dict with `success` (bool) and `data` (session/task payload),
    or `error` on failure.

    ## Examples
    - `libreoffice_writer(operation="status")` - live bridge session state
    - `libreoffice_writer(operation="live_write", prompt="Draft a memo about Q3")`
    """
    from .writer_ops import execute_libreoffice_writer_operation

    return await execute_libreoffice_writer_operation(
        operation,
        prompt=prompt,
        live_text=live_text,
        text=text,
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
        document_path=document_path,
    )


@mcp.tool(version="0.3.0", annotations={"readOnlyHint": False, "destructiveHint": False})
async def libreoffice_calc(
    operation: Annotated[str, Field(description="Calc live op: live_pivot_demo, type_cells, …")],
    input_path: Annotated[str | None, Field(description="Path for read_file")] = None,
    sheet_name: Annotated[str | None, Field(description="Sheet name")] = None,
    row: Annotated[int | None, Field(description="Cell row (0-based)")] = None,
    col: Annotated[int | None, Field(description="Cell col (0-based)")] = None,
    value: Annotated[str | float | None, Field(description="Cell value")] = None,
    start_row: Annotated[int, Field(description="Range start row")] = 0,
    start_col: Annotated[int, Field(description="Range start col")] = 0,
    end_row: Annotated[int | None, Field(description="Range end row")] = None,
    end_col: Annotated[int | None, Field(description="Range end col")] = None,
    values: Annotated[list[list[Any]] | None, Field(description="2D values for set_range")] = None,
    cells: Annotated[list[dict[str, Any]] | None, Field(description="Cells for type_cells")] = None,
    delay_sec: Annotated[float | None, Field(description="Delay between cells")] = None,
    max_rows: Annotated[int, Field(description="Max rows for read_file")] = 100,
    source_range: Annotated[str, Field(description="Pivot source A1:D7")] = "A1:D7",
    dest_row: Annotated[int, Field(description="Pivot destination row")] = 9,
    dest_col: Annotated[int, Field(description="Pivot destination col")] = 0,
    row_field: Annotated[str, Field(description="Pivot row field")] = "Region",
    data_field: Annotated[str, Field(description="Pivot data field")] = "Revenue",
    pivot_name: Annotated[str, Field(description="Pivot table name")] = "FleetPivot",
    typewriter_seed: Annotated[bool, Field(description="Typewriter demo data before pivot")] = True,
    macro_uri: Annotated[str | None, Field(description="UNO macro URI")] = None,
    macro_name: Annotated[str | None, Field(description="Macro name")] = None,
    macro_language: Annotated[str, Field(description="Basic or Python")] = "Basic",
    macro_location: Annotated[str, Field(description="application or document")] = "application",
    macro_library: Annotated[str | None, Field(description="Basic library")] = None,
    macro_module: Annotated[str | None, Field(description="Basic module")] = None,
    macro_args: Annotated[list[Any] | None, Field(description="Macro args")] = None,
) -> dict[str, Any]:
    """Live Calc portmanteau - cell typewriter + Data Pilot pivot (libreoffice-mcp-calc-bridge.oxt).

    ## Return Format
    Returns a dict with `success` (bool) and `data` (session/task payload),
    or `error` on failure.

    ## Examples
    - `libreoffice_calc(operation="live_pivot_demo")` - typewriter demo + pivot table
    - `libreoffice_calc(operation="read_file", input_path="C:/data/sheet.xlsx")`
    """
    from .calc_ops import execute_libreoffice_calc_operation

    return await execute_libreoffice_calc_operation(
        operation,
        input_path=input_path,
        sheet_name=sheet_name,
        row=row,
        col=col,
        value=value,
        start_row=start_row,
        start_col=start_col,
        end_row=end_row,
        end_col=end_col,
        values=values,
        cells=cells,
        delay_sec=delay_sec,
        max_rows=max_rows,
        source_range=source_range,
        dest_row=dest_row,
        dest_col=dest_col,
        row_field=row_field,
        data_field=data_field,
        pivot_name=pivot_name,
        typewriter_seed=typewriter_seed,
        macro_uri=macro_uri,
        macro_name=macro_name,
        macro_language=macro_language,
        macro_location=macro_location,
        macro_library=macro_library,
        macro_module=macro_module,
        macro_args=macro_args,
    )


@mcp.tool(version="0.2.0", annotations={"readOnlyHint": True, "destructiveHint": False})
async def libreoffice_help(
    topic: Annotated[
        str | None,
        Field(description="Optional topic: convert, merge, coworker, bridge, agentic"),
    ] = None,
) -> dict[str, Any]:
    """Help index for LibreOffice MCP operations and coworker PDF flows."""
    index = {
        "convert": "libreoffice(operation='convert', input_path='...', output_format='pdf')",
        "merge": "libreoffice(operation='merge', template='fleet-report.odt', placeholders={...})",
        "coworker": "fleet-report.odt, fleet-board-pack.odt, fleet-artifact-pack.odt",
        "bridge": "bridge_discover / bridge_call on extension MCP :8765",
        "agentic": "libreoffice_agentic_workflow(goal='...') with sampling",
    }
    if not topic:
        base = await execute_libreoffice_operation("help")
        base["topics"] = index
        return base
    if topic not in index:
        return {"error": f"Unknown topic: {topic}", "available": list(index.keys())}
    return {"topic": topic, "detail": index[topic]}


mcp.tool()(libreoffice_agentic_workflow)
register_prefab_tools(mcp)


@mcp.prompt
def libreoffice_quick_start() -> str:
    """Setup LibreOffice MCP - soffice path, dashboard, first convert."""
    return """LibreOffice MCP quick start:

1. Install LibreOffice 26.x; set LIBREOFFICE_MCP_SOFFICE_PATH if not auto-detected.
2. Optional: WriterAgent / mcp-libre on http://127.0.0.1:8765/mcp for live editing.
3. HTTP: uv run libreoffice-mcp --http --port 10981 - dashboard on :10983.
4. libreoffice(operation='status') then list_templates or convert a .md file to PDF.
5. For agentic flows: run Ollama, set LIBREOFFICE_MCP_SAMPLING_BASE_URL=http://127.0.0.1:11434/v1."""


@mcp.prompt
def libreoffice_coworker_pdf() -> str:
    """Coworker PDF deliverables - weekly report, board pack, artifact pack."""
    return """Coworker PDF workflow:

- Weekly report: merge fleet-report.odt (TITLE, DATE, SUMMARY, BODY) → PDF
- Board pack: fleet-board-pack.odt (KPI_TABLE, NARRATIVE, ACTION_ITEMS)
- Artifact pack: batch_pack multiple .md paths OR merge fleet-artifact-pack.odt

Use webapp Workflows page or libreoffice_agentic_workflow(goal='...')."""


@mcp.prompt
def libreoffice_convert_playbook() -> str:
    """Convert and batch pack playbook."""
    return """Conversion playbook:

- Single file: libreoffice(operation='convert', input_path='C:/path/doc.md', output_format='pdf')
- Markdown is rendered to HTML before PDF export.
- Batch: libreoffice(operation='batch_pack', input_paths=['a.md','b.md'], pack_title='Pack')
- Queue job for webapp tracking: queue_job=true on convert."""


@mcp.resource("resource://libreoffice-mcp/capabilities")
def libreoffice_capabilities_resource() -> str:
    """Machine-readable capability summary."""
    return (
        "LibreOffice MCP (FastMCP 3.3). Tools: libreoffice, libreoffice_writer, libreoffice_calc, "
        "libreoffice_help, libreoffice_agentic_workflow, prefabs. "
        "Sampling: LIBREOFFICE_MCP_SAMPLING_* or client LLM. Skills: skill://*/SKILL.md. "
        "REST: /health, /api/*. HTTP MCP: /mcp"
    )


def build_app() -> FastAPI:
    from .logging_utils import setup_ui_logging

    _mcp_http = mcp.http_app(path="/", transport="http", stateless_http=True)

    app = FastAPI(
        title="libreoffice-mcp",
        version=__version__,
        description="Headless LibreOffice convert + extension bridge",
        lifespan=_mcp_http.lifespan,
    )

    # Move original lifespan logic to startup/shutdown events
    @app.on_event("startup")
    async def _lo_startup():
        setup_ui_logging()
        settings.ensure_dirs()
        ensure_builtin_templates()
        log = logging.getLogger(__name__)
        log.info("libreoffice-mcp API starting on :%s", settings.port)

    @app.on_event("shutdown")
    async def _lo_shutdown():
        log = logging.getLogger(__name__)
        log.info("libreoffice-mcp API shutdown")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:10983",
            "http://localhost:10983",
            "http://goliath:10983",
            "http://tauri.localhost",
            "https://tauri.localhost",
            "tauri://localhost",
        ],
        allow_origin_regex=r"https?://(tauri\.localhost|localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|100\.\d+\.\d+\.\d+)(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.mount("/mcp", _mcp_http)
    app.include_router(api_router, prefix="/api")
    from .studio_routes import studio_router

    app.include_router(studio_router, prefix="/api")
    from .calc_bridge_routes import calc_router
    from .writer_bridge_routes import writer_router

    app.include_router(writer_router)
    app.include_router(calc_router)

    from .calc_session import calc_session_connected
    from .live_session import writer_session_connected

    @app.get("/health")
    async def health() -> dict[str, Any]:
        soffice = find_soffice()
        bridge = await probe_extension_bridge()
        return {
            "status": "healthy",
            "version": __version__,
            "fastmcp": "3.3+",
            "soffice_available": soffice is not None,
            "soffice_path": str(soffice) if soffice else None,
            "soffice_version": settings.soffice_product_version(),
            "extension_bridge_online": bridge.get("online", False),
            "extension_bridge_url": bridge.get("url"),
            "extension_tool_count": bridge.get("tool_count", 0),
            "writer_bridge_connected": writer_session_connected(),
            "calc_bridge_connected": calc_session_connected(),
            "output_dir": str(settings.output_dir),
            "templates_dir": str(settings.templates_dir),
            "sampling": sampling_handler.status(),
            "ports": {"backend": settings.port, "frontend": 10983},
        }

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="libreoffice-mcp")
    parser.add_argument("--http", action="store_true")
    parser.add_argument("--stdio", action="store_true")
    parser.add_argument("--port", type=int, default=settings.port)
    parser.add_argument("--host", type=str, default=settings.host)
    args = parser.parse_args()

    settings.ensure_dirs()

    if args.http or (not args.stdio and settings.transport == "http"):
        import uvicorn

        app = build_app()
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
