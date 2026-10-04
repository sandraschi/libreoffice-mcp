"""Register Prefab MCP App tools (FastMCP 3.3 / fleet SOTA §2.2)."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from prefab_ui.app import PrefabApp

from .bridge import health_summary
from .config import settings
from .prefabs import build_status_card, build_templates_card
from .templates import ensure_builtin_templates, list_templates

if TYPE_CHECKING:
    from fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register_prefab_tools(mcp: FastMCP) -> None:
    if os.getenv("LIBREOFFICE_MCP_PREFAB_APPS", "1").lower() in ("0", "false", "no"):
        logger.info("Prefab tools disabled via LIBREOFFICE_MCP_PREFAB_APPS=0")
        return

    @mcp.tool(app=True, annotations={"readOnlyHint": True, "destructiveHint": False})
    async def show_libreoffice_status_card() -> PrefabApp:
        """Show soffice and extension bridge health as a Prefab card."""
        summary = await health_summary()
        summary["soffice_version"] = settings.soffice_product_version()
        card = build_status_card(summary)
        return PrefabApp(view=card, title="LibreOffice Status")

    @mcp.tool(app=True, annotations={"readOnlyHint": True, "destructiveHint": False})
    async def show_templates_card() -> PrefabApp:
        """Show bundled fleet ODT templates as a Prefab gallery card."""
        ensure_builtin_templates()
        templates = list_templates()
        card = build_templates_card(templates)
        return PrefabApp(view=card, title="Fleet ODT Templates")
