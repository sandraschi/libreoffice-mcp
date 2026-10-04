"""Live Calc - cell typewriter and pivot demo in GUI."""

from __future__ import annotations

import asyncio
from typing import Any

from .calc_runtime import execute_calc_action, launch_calc_gui
from .calc_session import calc_session_connected, emit_calc_event
from .config import settings


def _demo_grid_cells() -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    headers = ["Region", "Product", "Units", "Revenue"]
    for c, h in enumerate(headers):
        cells.append({"row": 0, "col": c, "value": h})
    rows = [
        ["North", "Alpha", 12, 1200],
        ["North", "Beta", 8, 640],
        ["South", "Alpha", 20, 2000],
        ["South", "Gamma", 5, 750],
        ["East", "Beta", 15, 1350],
        ["West", "Gamma", 9, 1080],
    ]
    for r, row in enumerate(rows, start=1):
        for c, val in enumerate(row):
            cells.append({"row": r, "col": c, "value": val})
    return cells


async def live_type_cells(
    cells: list[dict[str, Any]],
    *,
    delay_sec: float | None = None,
    new_document: bool = True,
) -> dict[str, Any]:
    delay = delay_sec if delay_sec is not None else settings.live_calc_cell_delay_sec
    await emit_calc_event({"type": "start", "cells": len(cells)})

    if new_document:
        await execute_calc_action({"action": "new_document"}, timeout=30.0)

    for _ in range(35):
        if calc_session_connected():
            break
        await asyncio.sleep(1)

    result = await execute_calc_action(
        {"action": "type_cells", "cells": cells, "delay_sec": delay},
        timeout=max(90.0, len(cells) * (delay + 0.05) + 10),
    )
    if result.get("success"):
        await emit_calc_event({"type": "done", "typed_cells": len(cells), "mode": "live"})
    else:
        await emit_calc_event({"type": "error", "message": result.get("error")})
    return result


async def live_pivot_demo(
    *,
    launch_calc: bool = True,
    seed_first: bool = True,
    typewriter_seed: bool = True,
) -> dict[str, Any]:
    """Seed sales demo data (optional typewriter), then create Data Pilot pivot in GUI."""
    if launch_calc and not calc_session_connected():
        launch_calc_gui()

    await emit_calc_event({"type": "pivot_demo_start"})
    for _ in range(35):
        if calc_session_connected():
            break
        await asyncio.sleep(1)

    if not calc_session_connected():
        return {
            "success": False,
            "error": "Calc bridge offline. Install dist/libreoffice-mcp-calc-bridge.oxt and restart Calc.",
            "mode": "unavailable",
        }

    await execute_calc_action({"action": "new_document"}, timeout=25.0)

    if seed_first:
        if typewriter_seed:
            await live_type_cells(_demo_grid_cells(), new_document=False)
        else:
            await execute_calc_action({"action": "seed_demo_data"}, timeout=30.0)

    await emit_calc_event({"type": "creating_pivot"})
    pivot = await execute_calc_action(
        {
            "action": "create_pivot",
            "source_range": "A1:D7",
            "dest_row": 9,
            "dest_col": 0,
            "row_field": "Region",
            "data_field": "Revenue",
            "pivot_name": "FleetPivot",
        },
        timeout=60.0,
    )
    if pivot.get("success"):
        await emit_calc_event({"type": "pivot_done", "data": pivot.get("data")})
    return {
        **pivot,
        "message": "Pivot table inserted in Calc - check the sheet below your data.",
    }
