"""Prefab card builders for libreoffice-mcp."""

from __future__ import annotations

from typing import Any

from prefab_ui.components import Badge, Card, CardContent, CardHeader, CardTitle, Metric, Row
from prefab_ui.components.base import Component


def build_status_card(data: dict[str, Any]) -> Card:
    """Health card for soffice + extension bridge."""
    lo_ok = bool(data.get("soffice_found") or data.get("soffice_available"))
    bridge = data.get("extension_bridge") or {}
    bridge_ok = bool(bridge.get("online"))

    rows = [
        Row(
            children=[
                Metric(label="soffice", value="Ready" if lo_ok else "Missing"),
                Metric(label="Path", value=str(data.get("soffice_path") or "-")[:48]),
                Metric(label="Version", value=str(data.get("soffice_version") or "-")),
            ]
        ),
        Row(
            children=[
                Metric(label="Bridge", value="Online" if bridge_ok else "Offline"),
                Metric(label="URL", value=str(bridge.get("url") or "-")[:48]),
                Metric(label="Tools", value=str(bridge.get("tool_count", 0))),
            ]
        ),
    ]
    badges: list[Component] = [Badge(label="LibreOffice MCP")]
    if lo_ok and bridge_ok:
        badges.append(Badge(label="Full stack"))
    elif lo_ok:
        badges.append(Badge(label="Headless only"))

    body: list[Component] = []
    body.extend(rows)
    body.append(Row(children=badges))
    header: list[Component] = [CardTitle("LibreOffice Status")]
    top: list[Component] = [
        CardHeader(children=header),
        CardContent(children=body),
    ]
    return Card(children=top)


def build_templates_card(templates: list[dict[str, Any]]) -> Card:
    """Gallery card for bundled ODT templates."""
    rows = []
    for t in templates[:12]:
        ph = ", ".join(t.get("placeholders") or [])[:60]
        rows.append(
            Row(
                children=[
                    Metric(label="Template", value=t.get("name", "?")),
                    Metric(label="Placeholders", value=ph or "-"),
                ]
            )
        )
    gallery: list[Component] = []
    gallery.extend(rows)
    count: list[Component] = [Badge(label=f"{len(templates)} templates")]
    gallery.append(Row(children=count))
    thead: list[Component] = [CardTitle("Fleet ODT Templates")]
    ttop: list[Component] = [
        CardHeader(children=thead),
        CardContent(children=gallery),
    ]
    return Card(children=ttop)
