"""In-process Calc session task queue (mirrors Writer live_session)."""

from __future__ import annotations

import asyncio
import time
import uuid
from collections import deque
from typing import Any

_calc_tasks: dict[str, dict[str, Any]] = {}
_session_last_heartbeat: float = 0.0
_calc_subscribers: list[asyncio.Queue[dict[str, Any]]] = []
_calc_events_log: deque[dict[str, Any]] = deque(maxlen=500)

HEARTBEAT_TTL_SEC = 10.0


def calc_session_connected() -> bool:
    return (time.monotonic() - _session_last_heartbeat) < HEARTBEAT_TTL_SEC


def note_calc_heartbeat() -> None:
    global _session_last_heartbeat
    _session_last_heartbeat = time.monotonic()


def subscribe_calc_events(maxsize: int = 256) -> asyncio.Queue[dict[str, Any]]:
    q: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=maxsize)
    _calc_subscribers.append(q)
    return q


def unsubscribe_calc_events(q: asyncio.Queue[dict[str, Any]]) -> None:
    if q in _calc_subscribers:
        _calc_subscribers.remove(q)


async def emit_calc_event(event: dict[str, Any]) -> None:
    event = {**event, "ts": time.time()}
    _calc_events_log.append(event)
    dead: list[asyncio.Queue[dict[str, Any]]] = []
    for q in _calc_subscribers:
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        unsubscribe_calc_events(q)


def recent_calc_events(limit: int = 50) -> list[dict[str, Any]]:
    return list(_calc_events_log)[-limit:]


def get_pending_calc_task() -> dict[str, Any] | None:
    note_calc_heartbeat()
    for task_id, task in _calc_tasks.items():
        if not task["done"] and task["result"] is None:
            return {"id": task_id, "action": task["action"]}
    return None


def submit_calc_result(task_id: str, body: dict[str, Any]) -> None:
    note_calc_heartbeat()
    if task_id in _calc_tasks:
        _calc_tasks[task_id]["result"] = body
        _calc_tasks[task_id]["done"] = True


async def queue_calc_action(
    action: dict[str, Any],
    *,
    timeout: float = 90.0,
) -> dict[str, Any]:
    """Queue action for Calc .oxt bridge; wait for result."""
    task_id = str(uuid.uuid4())[:8]
    _calc_tasks[task_id] = {
        "id": task_id,
        "action": action,
        "result": None,
        "done": False,
    }

    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        await asyncio.sleep(0.12)
        task = _calc_tasks.get(task_id)
        if task and task["done"]:
            result = task["result"] or {}
            _calc_tasks.pop(task_id, None)
            return {
                "success": bool(result.get("success", False)),
                "output": result.get("output", ""),
                "error": result.get("error"),
                "data": result.get("data"),
                "session_used": True,
                "mode": "live",
            }

    _calc_tasks.pop(task_id, None)
    return {
        "success": False,
        "error": "Calc bridge timed out. Open Calc and install libreoffice-mcp-calc-bridge.oxt.",
        "session_used": False,
        "mode": "unavailable",
    }


def calc_session_status() -> dict[str, Any]:
    pending = sum(1 for t in _calc_tasks.values() if not t["done"])
    return {
        "connected": calc_session_connected(),
        "pending_tasks": pending,
        "last_heartbeat_sec_ago": round(time.monotonic() - _session_last_heartbeat, 2)
        if _session_last_heartbeat
        else None,
    }
