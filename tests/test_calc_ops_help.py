import pytest

from libreoffice_mcp.calc_ops import execute_libreoffice_calc_operation


@pytest.mark.asyncio
async def test_calc_help_lists_operations():
    out = await execute_libreoffice_calc_operation("help")
    assert out["success"] is True
    assert "live_pivot_demo" in out["operations"]
