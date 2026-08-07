"""Live Studio API tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from libreoffice_mcp.server import build_app


@pytest.fixture
def studio_env(tmp_path, monkeypatch):
    from libreoffice_mcp import config

    out = tmp_path / "output"
    out.mkdir()
    monkeypatch.setattr(config.settings, "templates_dir", tmp_path / "templates")
    monkeypatch.setattr(config.settings, "output_dir", out)
    monkeypatch.setattr(config.settings, "data_dir", tmp_path / "data")
    client = TestClient(build_app())
    return client, out


def test_studio_session(studio_env):
    client, _out = studio_env
    r = client.get("/api/studio/session")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert "soffice_available" in data
    assert "writer_bridge_connected" in data
    assert "calc_bridge_connected" in data
    assert "output_dir" in data
    assert data["live_pages"]["live_write"] == "/live-write"
    assert data["live_pages"]["live_calc"] == "/live-calc"
    assert isinstance(data["recent_outputs"], list)


def test_studio_open_in_app_launch(studio_env, monkeypatch):
    client, _out = studio_env
    mock_popen = MagicMock()
    monkeypatch.setattr("libreoffice_mcp.lo_gui.subprocess.Popen", mock_popen)
    monkeypatch.setattr(
        "libreoffice_mcp.lo_gui.find_soffice",
        lambda: Path("C:/Program Files/LibreOffice/program/soffice.exe"),
    )

    r = client.post("/api/studio/open-in-app", json={"family": "writer"})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["family"] == "writer"
    mock_popen.assert_called_once()


def test_studio_open_in_app_with_file(studio_env, monkeypatch):
    client, out = studio_env
    sample = out / "report.odt"
    sample.write_text("sample", encoding="utf-8")

    mock_popen = MagicMock()
    monkeypatch.setattr("libreoffice_mcp.lo_gui.subprocess.Popen", mock_popen)
    monkeypatch.setattr(
        "libreoffice_mcp.lo_gui.find_soffice",
        lambda: Path("C:/Program Files/LibreOffice/program/soffice.exe"),
    )

    r = client.post(
        "/api/studio/open-in-app",
        json={"family": "writer", "path": "report.odt"},
    )
    assert r.status_code == 200
    assert r.json()["path"] is not None
    args = mock_popen.call_args[0][0]
    assert str(sample) in args


def test_studio_open_in_app_rejects_traversal(studio_env, monkeypatch):
    client, _out = studio_env
    monkeypatch.setattr(
        "libreoffice_mcp.lo_gui.find_soffice",
        lambda: Path("C:/Program Files/LibreOffice/program/soffice.exe"),
    )

    r = client.post(
        "/api/studio/open-in-app",
        json={"family": "calc", "path": "../secrets.ods"},
    )
    assert r.status_code == 400


def test_studio_open_in_app_no_soffice(studio_env, monkeypatch):
    client, _out = studio_env
    monkeypatch.setattr("libreoffice_mcp.lo_gui.find_soffice", lambda: None)

    r = client.post("/api/studio/open-in-app", json={"family": "impress"})
    assert r.status_code == 400
    assert "soffice" in r.json()["detail"].lower()
