"""In-process Writer session task queue (Blender-mcp bridge pattern)."""

from __future__ import annotations

import asyncio
import time
import uuid
from collections import deque
from typing import Any

_writer_tasks: dict[str, dict[str, Any]] = {}
_session_last_heartbeat: float = 0.0
_live_subscribers: list[asyncio.Queue[dict[str, Any]]] = []
_live_events_log: deque[dict[str, Any]] = deque(maxlen=500)

HEARTBEAT_TTL_SEC = 10.0


def writer_session_connected() -> bool:
    return (time.monotonic() - _session_last_heartbeat) < HEARTBEAT_TTL_SEC


def note_writer_heartbeat() -> None:
    global _session_last_heartbeat
    _session_last_heartbeat = time.monotonic()


def subscribe_live_events(maxsize: int = 256) -> asyncio.Queue[dict[str, Any]]:
    q: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=maxsize)
    _live_subscribers.append(q)
    return q


def unsubscribe_live_events(q: asyncio.Queue[dict[str, Any]]) -> None:
    if q in _live_subscribers:
        _live_subscribers.remove(q)


async def emit_live_event(event: dict[str, Any]) -> None:
    event = {**event, "ts": time.time()}
    _live_events_log.append(event)
    dead: list[asyncio.Queue[dict[str, Any]]] = []
    for q in _live_subscribers:
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        unsubscribe_live_events(q)


def recent_live_events(limit: int = 50) -> list[dict[str, Any]]:
    return list(_live_events_log)[-limit:]


def get_pending_writer_task() -> dict[str, Any] | None:
    note_writer_heartbeat()
    for task_id, task in _writer_tasks.items():
        if not task["done"] and task["result"] is None:
            return {
                "id": task_id,
                "action": task["action"],
            }
    return None


def submit_writer_result(task_id: str, body: dict[str, Any]) -> None:
    note_writer_heartbeat()
    if task_id in _writer_tasks:
        _writer_tasks[task_id]["result"] = body
        _writer_tasks[task_id]["done"] = True


async def queue_writer_action(
    action: dict[str, Any],
    *,
    timeout: float = 45.0,
) -> dict[str, Any]:
    """Queue a structured action for the Writer bridge macro; wait for result."""
    task_id = str(uuid.uuid4())[:8]
    _writer_tasks[task_id] = {
        "id": task_id,
        "action": action,
        "result": None,
        "done": False,
    }

    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        await asyncio.sleep(0.12)
        task = _writer_tasks.get(task_id)
        if task and task["done"]:
            result = task["result"] or {}
            _writer_tasks.pop(task_id, None)
            return {
                "success": bool(result.get("success", False)),
                "output": result.get("output", ""),
                "error": result.get("error"),
                "session_used": True,
                "mode": "live",
            }

    _writer_tasks.pop(task_id, None)
    return {
        "success": False,
        "error": "Writer bridge timed out waiting for macro result.",
        "session_used": False,
        "mode": "unavailable",
    }


def writer_session_status() -> dict[str, Any]:
    pending = sum(1 for t in _writer_tasks.values() if not t["done"])
    return {
        "connected": writer_session_connected(),
        "pending_tasks": pending,
        "last_heartbeat_sec_ago": round(time.monotonic() - _session_last_heartbeat, 2)
        if _session_last_heartbeat
        else None,
    }
