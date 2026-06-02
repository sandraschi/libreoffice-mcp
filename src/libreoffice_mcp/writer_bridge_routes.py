"""HTTP routes for Writer live session bridge (poll/result like blender-mcp)."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .live_session import (
    get_pending_writer_task,
    note_writer_heartbeat,
    recent_live_events,
    submit_writer_result,
    subscribe_live_events,
    unsubscribe_live_events,
    writer_session_connected,
    writer_session_status,
)
from .live_write import live_type_text, live_write
from .writer_runtime import launch_writer_gui

writer_router = APIRouter()


class LiveWriteRequest(BaseModel):
    prompt: str = Field(description="What to write (e.g. a short story about butterflies)")
    wpm: float = Field(default=180.0, description="Typewriter speed (words per minute)")
    max_words: int = Field(default=400)
    prefer_session: bool = True
    headless_fallback: bool = True
    launch_writer: bool = True


class LiveTypeRequest(BaseModel):
    text: str
    wpm: float = 180.0
    prefer_session: bool = True
    headless_fallback: bool = True
    new_document: bool = True


class WriterResultBody(BaseModel):
    id: str
    success: bool = True
    output: str = ""
    error: str | None = None


def register_writer_bridge_routes(app) -> None:
    """Mount bridge at /api/v1/writer/* and live SSE at /api/live/*."""
    app.include_router(writer_router)


@writer_router.get("/api/v1/writer/pending")
async def writer_pending() -> dict[str, Any]:
    task = get_pending_writer_task()
    return task or {}


@writer_router.post("/api/v1/writer/result")
async def writer_result(body: WriterResultBody) -> dict[str, Any]:
    submit_writer_result(body.id, body.model_dump())
    return {"success": True}


@writer_router.post("/api/v1/writer/heartbeat")
async def writer_heartbeat() -> dict[str, Any]:
    note_writer_heartbeat()
    return {"success": True, "connected": True}


@writer_router.get("/api/v1/writer/session")
async def writer_session() -> dict[str, Any]:
    return {"success": True, **writer_session_status()}


@writer_router.post("/api/live/write")
async def api_live_write(body: LiveWriteRequest) -> dict[str, Any]:
    result = await live_write(
        body.prompt,
        wpm=body.wpm,
        max_words=body.max_words,
        prefer_session=body.prefer_session,
        headless_fallback=body.headless_fallback,
        launch_writer=body.launch_writer,
    )
    return {"success": result.get("success", False), "data": result}


@writer_router.post("/api/live/type")
async def api_live_type(body: LiveTypeRequest) -> dict[str, Any]:
    result = await live_type_text(
        body.text,
        wpm=body.wpm,
        prefer_session=body.prefer_session,
        headless_fallback=body.headless_fallback,
        new_document=body.new_document,
    )
    return {"success": result.get("success", False), "data": result}


@writer_router.post("/api/live/launch-writer")
async def api_launch_writer() -> dict[str, Any]:
    return launch_writer_gui()


@writer_router.get("/api/live/events")
async def api_live_events(request: Request):
    """SSE stream of typewriter / live-write progress."""

    async def stream():
        q = subscribe_live_events()
        try:
            for ev in recent_live_events(20):
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
            unsubscribe_live_events(q)

    return StreamingResponse(stream(), media_type="text/event-stream")


@writer_router.get("/api/live/status")
async def api_live_status() -> dict[str, Any]:
    return {
        "success": True,
        "writer_bridge_connected": writer_session_connected(),
        **writer_session_status(),
        "recent_events": recent_live_events(10),
    }
