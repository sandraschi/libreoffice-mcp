"""Portmanteau dispatch for libreoffice_calc(operation=…)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, cast, get_args

from .calc_runtime import execute_calc_action, launch_calc_gui
from .calc_session import calc_session_status as get_calc_session_status
from .live_calc import live_pivot_demo, live_type_cells
from .macro_ops import (
    MacroLanguage,
    MacroLocation,
    build_macro_uri,
    macro_action_payload,
)
from .spreadsheet_read import read_spreadsheet_data

CalcOp = Literal[
    "status",
    "help",
    "launch_calc",
    "read_file",
    "set_cell",
    "set_range",
    "type_cells",
    "get_range",
    "sheet_info",
    "seed_demo",
    "create_pivot",
    "live_type_grid",
    "live_pivot_demo",
    "run_macro",
    "run_python_macro",
]


async def execute_libreoffice_calc_operation(
    operation: str,
    *,
    input_path: str | None = None,
    sheet_name: str | None = None,
    row: int | None = None,
    col: int | None = None,
    value: str | float | None = None,
    start_row: int = 0,
    start_col: int = 0,
    end_row: int | None = None,
    end_col: int | None = None,
    values: list[list[Any]] | None = None,
    cells: list[dict[str, Any]] | None = None,
    delay_sec: float | None = None,
    max_rows: int = 100,
    source_range: str = "A1:D7",
    dest_row: int = 9,
    dest_col: int = 0,
    row_field: str = "Region",
    data_field: str = "Revenue",
    pivot_name: str = "FleetPivot",
    typewriter_seed: bool = True,
    macro_uri: str | None = None,
    macro_name: str | None = None,
    macro_language: str = "Basic",
    macro_location: str = "application",
    macro_library: str | None = None,
    macro_module: str | None = None,
    macro_args: list[Any] | None = None,
) -> dict[str, Any]:
    if operation == "status":
        return {"success": True, "data": get_calc_session_status()}

    if operation == "help":
        return {
            "success": True,
            "message": "libreoffice_calc — live Calc bridge + headless spreadsheet read",
            "operations": list(get_args(CalcOp)),
            "install": "dist/libreoffice-mcp-calc-bridge.oxt + just webapp",
            "live_endpoints": [
                "/api/live/calc/type-cells",
                "/api/live/calc/pivot-demo",
                "/api/live/calc/events",
            ],
        }

    if operation == "launch_calc":
        return launch_calc_gui(
            document_path=Path(input_path) if input_path else None,
        )

    if operation == "read_file":
        if not input_path:
            return {"success": False, "error": "input_path required for read_file"}
        data = read_spreadsheet_data(
            Path(input_path),
            sheet_name=sheet_name,
            max_rows=max_rows,
        )
        return {"success": data.get("success", False), "data": data}

    if operation == "live_type_grid":
        grid = cells
        if not grid and values:
            grid = []
            for r, row_vals in enumerate(values):
                for c, val in enumerate(row_vals):
                    grid.append({"row": start_row + r, "col": start_col + c, "value": val})
        if not grid:
            return {"success": False, "error": "cells or values required for live_type_grid"}
        result = await live_type_cells(grid, delay_sec=delay_sec, new_document=True)
        return {"success": result.get("success", False), "message": result.get("message", ""), "next_steps": result.get("next_steps", []), "data": result}

    if operation == "live_pivot_demo":
        result = await live_pivot_demo(typewriter_seed=typewriter_seed)
        return {"success": result.get("success", False), "message": result.get("message", ""), "next_steps": result.get("next_steps", []), "data": result}

    if operation == "set_cell":
        if row is None or col is None:
            return {"success": False, "error": "row and col required for set_cell"}
        result = await execute_calc_action(
            {
                "action": "set_cell",
                "row": row,
                "col": col,
                "value": value if value is not None else "",
                "sheet": sheet_name,
            }
        )
        return {"success": result.get("success", False), "message": result.get("message", ""), "next_steps": result.get("next_steps", []), "data": result}

    if operation == "set_range":
        if not values:
            return {"success": False, "error": "values required for set_range"}
        result = await execute_calc_action(
            {
                "action": "set_range",
                "start_row": start_row,
                "start_col": start_col,
                "values": values,
                "sheet": sheet_name,
            }
        )
        return {"success": result.get("success", False), "message": result.get("message", ""), "next_steps": result.get("next_steps", []), "data": result}

    if operation == "type_cells":
        if not cells:
            return {"success": False, "error": "cells required for type_cells"}
        result = await execute_calc_action(
            {
                "action": "type_cells",
                "cells": cells,
                "delay_sec": delay_sec or 0.08,
                "sheet": sheet_name,
            },
            timeout=max(120.0, len(cells) * 0.15),
        )
        return {"success": result.get("success", False), "message": result.get("message", ""), "next_steps": result.get("next_steps", []), "data": result}

    if operation == "get_range":
        result = await execute_calc_action(
            {
                "action": "get_range",
                "start_row": start_row,
                "start_col": start_col,
                "end_row": end_row if end_row is not None else start_row,
                "end_col": end_col if end_col is not None else start_col,
                "sheet": sheet_name,
            }
        )
        return {"success": result.get("success", False), "message": result.get("message", ""), "next_steps": result.get("next_steps", []), "data": result}

    if operation == "sheet_info":
        result = await execute_calc_action({"action": "sheet_info", "sheet": sheet_name})
        return {"success": result.get("success", False), "message": result.get("message", ""), "next_steps": result.get("next_steps", []), "data": result}

    if operation == "seed_demo":
        result = await execute_calc_action({"action": "seed_demo_data"})
        return {"success": result.get("success", False), "message": result.get("message", ""), "next_steps": result.get("next_steps", []), "data": result}

    if operation == "create_pivot":
        result = await execute_calc_action(
            {
                "action": "create_pivot",
                "source_range": source_range,
                "dest_row": dest_row,
                "dest_col": dest_col,
                "row_field": row_field,
                "data_field": data_field,
                "pivot_name": pivot_name,
                "sheet": sheet_name,
            },
            timeout=60.0,
        )
        return {"success": result.get("success", False), "message": result.get("message", ""), "next_steps": result.get("next_steps", []), "data": result}

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
        result = await execute_calc_action(action, timeout=60.0)
        return {"success": result.get("success", False), "message": result.get("message", ""), "next_steps": result.get("next_steps", []), "data": result}

    return {"success": False, "error": f"Unknown calc operation: {operation}"}
