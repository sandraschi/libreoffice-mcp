"""HTTP routes for Calc live bridge."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .calc_runtime import launch_calc_gui
from .calc_session import (
    calc_session_connected,
    calc_session_status,
    get_pending_calc_task,
    note_calc_heartbeat,
    recent_calc_events,
    submit_calc_result,
    subscribe_calc_events,
    unsubscribe_calc_events,
)
from .live_calc import live_pivot_demo, live_type_cells

calc_router = APIRouter()


class CalcResultBody(BaseModel):
    id: str
    success: bool = True
    output: str = ""
    error: str | None = None
    data: dict[str, Any] | None = None


class LiveTypeCellsRequest(BaseModel):
    cells: list[dict[str, Any]] = Field(default_factory=list)
    delay_sec: float = 0.08
    new_document: bool = True


class LivePivotDemoRequest(BaseModel):
    launch_calc: bool = True
    seed_first: bool = True
    typewriter_seed: bool = True


def register_calc_bridge_routes(app) -> None:
    app.include_router(calc_router)


@calc_router.get("/api/v1/calc/pending")
async def calc_pending() -> dict[str, Any]:
    task = get_pending_calc_task()
    return task or {}


@calc_router.post("/api/v1/calc/result")
async def calc_result(body: CalcResultBody) -> dict[str, Any]:
    submit_calc_result(body.id, body.model_dump())
    return {"success": True}


@calc_router.post("/api/v1/calc/heartbeat")
async def calc_heartbeat() -> dict[str, Any]:
    note_calc_heartbeat()
    return {"success": True, "connected": True}


@calc_router.get("/api/v1/calc/session")
async def calc_session() -> dict[str, Any]:
    return {"success": True, **calc_session_status()}


@calc_router.post("/api/live/calc/type-cells")
async def api_live_type_cells(body: LiveTypeCellsRequest) -> dict[str, Any]:
    result = await live_type_cells(
        body.cells,
        delay_sec=body.delay_sec,
        new_document=body.new_document,
    )
    return {
        "success": result.get("success", False),
        "message": result.get("message", ""),
        "next_steps": result.get("next_steps", []),
        "data": result,
    }


@calc_router.post("/api/live/calc/pivot-demo")
async def api_live_pivot_demo(body: LivePivotDemoRequest) -> dict[str, Any]:
    result = await live_pivot_demo(
        launch_calc=body.launch_calc,
        seed_first=body.seed_first,
        typewriter_seed=body.typewriter_seed,
    )
    return {
        "success": result.get("success", False),
        "message": result.get("message", ""),
        "next_steps": result.get("next_steps", []),
        "data": result,
    }


@calc_router.post("/api/live/launch-calc")
async def api_launch_calc() -> dict[str, Any]:
    return launch_calc_gui()


@calc_router.get("/api/live/calc/events")
async def api_calc_events(request: Request):
    async def stream():
        q = subscribe_calc_events()
        try:
            for ev in recent_calc_events(20):
                yield f"data: {json.dumps(ev)}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(q.get(), timeout=25.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except TimeoutError:
                    yield f"data: {json.dumps({'type': 'ping'})}\n\n"
        finally:
            unsubscribe_calc_events(q)

    return StreamingResponse(stream(), media_type="text/event-stream")


@calc_router.get("/api/live/calc/status")
async def api_calc_live_status() -> dict[str, Any]:
    return {
        "success": True,
        "calc_bridge_connected": calc_session_connected(),
        **calc_session_status(),
        "recent_events": recent_calc_events(10),
    }
