"""Tests for libreoffice-mcp."""

from pathlib import Path

import pytest

from libreoffice_mcp.config import Settings
from libreoffice_mcp.headless import find_soffice


def test_find_soffice_returns_path_or_none():
    result = find_soffice()
    assert result is None or Path(result).name.lower().startswith("soffice")


def test_settings_custom_soffice(tmp_path):
    fake = tmp_path / "soffice.exe"
    fake.write_text("", encoding="utf-8")
    s = Settings(soffice_path=str(fake))
    assert s.resolve_soffice() == fake


@pytest.mark.asyncio
async def test_libreoffice_help():
    from libreoffice_mcp.server import libreoffice

    r = await libreoffice(operation="help")
    assert r["success"] is True
    assert "convert" in r["operations"]
