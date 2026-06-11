import asyncio

import pytest

from libreoffice_mcp import calc_session
from libreoffice_mcp.calc_session import (
    calc_session_connected,
    get_pending_calc_task,
    note_calc_heartbeat,
    queue_calc_action,
    submit_calc_result,
)


@pytest.fixture(autouse=True)
def _reset_calc_session():
    calc_session._calc_tasks.clear()
    calc_session._calc_events_log.clear()
    calc_session._calc_subscribers.clear()
    calc_session._session_last_heartbeat = 0.0
    yield


@pytest.mark.asyncio
async def test_calc_queue_roundtrip():
    note_calc_heartbeat()
    assert calc_session_connected()

    async def run():
        return await queue_calc_action({"action": "sheet_info"}, timeout=2.0)

    task = asyncio.create_task(run())
    await asyncio.sleep(0.2)
    pending = get_pending_calc_task()
    assert pending is not None
    submit_calc_result(
        pending["id"],
        {"success": True, "output": "ok", "data": {"sheet": "Sheet1"}},
    )
    result = await task
    assert result["success"] is True
    assert result.get("data", {}).get("sheet") == "Sheet1"
