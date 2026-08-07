"""Execute Writer actions — live bridge preferred, headless fallback."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any

from .bridge import call_extension_tool, probe_extension_bridge
from .config import settings
from .headless import convert_file, find_soffice
from .live_session import queue_writer_action

log = logging.getLogger(__name__)

_EXTENSION_INSERT_TOOLS = (
    "insert_text",
    "append_text",
    "type_text",
    "writer_insert_text",
    "writer_append",
)


async def _try_extension_insert(
    text: str, *, bridge_url: str | None = None
) -> dict[str, Any] | None:
    probe = await probe_extension_bridge(bridge_url)
    if not probe.get("online"):
        return None
    tool_names = {t["name"] for t in probe.get("tools", [])}
    for name in _EXTENSION_INSERT_TOOLS:
        if name in tool_names:
            data = await call_extension_tool(
                name,
                {"text": text},
                url=bridge_url,
            )
            if data.get("success"):
                return {
                    "success": True,
                    "mode": "extension_bridge",
                    "tool": name,
                    "session_used": True,
                    "data": data,
                }
    return None


async def execute_writer_action(
    action: dict[str, Any],
    *,
    prefer_session: bool = True,
    headless_fallback: bool = False,
    bridge_url: str | None = None,
    timeout: float = 15.0,
) -> dict[str, Any]:
    """Run a structured Writer action in live GUI when bridge is connected."""
    if prefer_session and action.get("action") == "insert_text":
        ext = await _try_extension_insert(str(action.get("text", "")), bridge_url=bridge_url)
        if ext:
            return ext

    if prefer_session:
        result = await queue_writer_action(action, timeout=timeout)
        if result.get("success") and result.get("session_used"):
            return result
        if not headless_fallback:
            return result

    if not headless_fallback:
        return {
            "success": False,
            "error": "No live Writer session. Run the bridge macro or enable extension MCP.",
            "session_used": False,
            "mode": "unavailable",
        }

    return {
        "success": False,
        "error": f"No headless fallback for action {action.get('action')}",
        "session_used": False,
        "mode": "unavailable",
    }


def launch_writer_gui(*, document_path: Path | None = None) -> dict[str, Any]:
    """Open LibreOffice Writer (optional document)."""
    soffice = find_soffice()
    if soffice is None:
        return {"success": False, "error": "soffice not found"}
    cmd = [str(soffice), "--writer"]
    if document_path and document_path.is_file():
        cmd.append(str(document_path))
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {
            "success": True,
            "message": "Writer launched",
            "path": str(document_path) if document_path else None,
        }
    except OSError as exc:
        return {"success": False, "error": str(exc)}


async def headless_write_markdown(
    text: str,
    *,
    output_stem: str = "live-write",
    output_format: str = "odt",
) -> dict[str, Any]:
    """Fallback: write markdown file and convert when live bridge unavailable."""
    settings.ensure_dirs()
    md_path = settings.output_dir / f"{output_stem}.md"
    md_path.write_text(text, encoding="utf-8")
    result = convert_file(md_path, output_format)
    if result.get("success") and result.get("output"):
        out = Path(result["output"])
        launch_writer_gui(document_path=out)
        return {
            "success": True,
            "mode": "headless_fallback",
            "session_used": False,
            "markdown": str(md_path),
            "output": str(out),
            "message": "Live bridge offline — opened converted document in Writer.",
        }
    return {
        "success": bool(result.get("success")),
        "mode": "headless_fallback",
        "session_used": False,
        "data": result,
    }
