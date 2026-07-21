"""Bridge to LibreOffice extension MCP servers (WriterAgent, mcp-libre, Nelson MCP)."""

from __future__ import annotations

from typing import Any

import httpx
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

from .config import settings


async def probe_extension_bridge(url: str | None = None) -> dict[str, Any]:
    """Check whether an extension-hosted MCP server is reachable."""
    target = (url or settings.extension_bridge_url).rstrip("/")
    if not target.endswith("/mcp"):
        target = f"{target}/mcp"

    try:
        async with await _client(target) as client:
            tools = await client.list_tools()
            return {
                "success": True,
                "online": True,
                "url": target,
                "tool_count": len(tools),
                "tools": [
                    {"name": t.name, "description": (t.description or "")[:120]} for t in tools[:25]
                ],
            }
    except Exception as exc:
        return {
            "success": True,
            "online": False,
            "url": target,
            "tool_count": 0,
            "error": str(exc)[:300],
            "hint": "Install WriterAgent or mcp-libre .oxt; enable MCP on port 8765",
        }


async def call_extension_tool(
    tool: str,
    arguments: dict[str, Any] | None = None,
    *,
    url: str | None = None,
) -> dict[str, Any]:
    """Proxy a tool call to the extension MCP server."""
    target = (url or settings.extension_bridge_url).rstrip("/")
    if not target.endswith("/mcp"):
        target = f"{target}/mcp"
    args = arguments or {}

    try:
        async with await _client(target) as client:
            result = await client.call_tool(tool, args)
            parts = []
            for block in result.content:
                if hasattr(block, "text"):
                    parts.append(block.text)
            return {
                "success": not result.is_error,
                "tool": tool,
                "url": target,
                "content": parts,
                "is_error": result.is_error,
            }
    except Exception as exc:
        return {"success": False, "tool": tool, "url": target, "error": str(exc)}


async def health_summary() -> dict[str, Any]:
    soffice = find_soffice_path()
    bridge = await probe_extension_bridge()
    return {
        "soffice_found": soffice is not None,
        "soffice_path": str(soffice) if soffice else None,
        "extension_bridge": bridge,
    }


def find_soffice_path() -> str | None:
    p = settings.resolve_soffice()
    return str(p) if p else None


async def _client(url: str) -> Client:
    return Client(StreamableHttpTransport(url))


async def http_ping(url: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(url.replace("/mcp", "/") if "/mcp" in url else url)
            return r.status_code < 500
    except Exception:
        return False
