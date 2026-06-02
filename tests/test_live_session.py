"""Tests for Writer live session bridge."""

from __future__ import annotations

import pytest

from libreoffice_mcp import live_session


@pytest.fixture(autouse=True)
def _reset_session():
    live_session._writer_tasks.clear()
    live_session._live_events_log.clear()
    live_session._live_subscribers.clear()
    live_session._session_last_heartbeat = 0.0
    yield


def test_writer_session_status_disconnected():
    st = live_session.writer_session_status()
    assert st["connected"] is False


def test_pending_and_result():
    live_session._writer_tasks["abc"] = {
        "id": "abc",
        "action": {"action": "insert_text", "text": "hi"},
        "result": None,
        "done": False,
    }
    pending = live_session.get_pending_writer_task()
    assert pending is not None
    assert pending["id"] == "abc"
    live_session.submit_writer_result("abc", {"success": True, "output": "ok"})
    assert live_session._writer_tasks["abc"]["done"] is True


@pytest.mark.asyncio
async def test_emit_live_event():
    q = live_session.subscribe_live_events()
    await live_session.emit_live_event({"type": "test", "text": "x"})
    assert not q.empty()
    ev = q.get_nowait()
    assert ev["type"] == "test"
    live_session.unsubscribe_live_events(q)
