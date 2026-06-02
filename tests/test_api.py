"""REST API tests (FastAPI TestClient — no live soffice required)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from libreoffice_mcp.server import build_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    from libreoffice_mcp import config

    monkeypatch.setattr(config.settings, "templates_dir", tmp_path / "templates")
    monkeypatch.setattr(config.settings, "output_dir", tmp_path / "output")
    return TestClient(build_app())


def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "soffice_available" in data
    assert "soffice_version" in data
    assert "extension_bridge_online" in data
    assert data["ports"]["backend"] == 10981
    assert data["ports"]["frontend"] == 10983


def test_api_tools(client: TestClient):
    r = client.get("/api/tools")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    names = {t["name"] for t in body["tools"]}
    assert "libreoffice" in names
    portmanteau = next(t for t in body["tools"] if t["name"] == "libreoffice")
    assert portmanteau["kind"] == "portmanteau"
    op_names = {op["name"] for op in portmanteau["operations"]}
    assert "convert" in op_names
    assert "merge" in op_names
    assert "pdf_merge" in op_names
    assert "convert_batch" in op_names


def test_api_help(client: TestClient):
    r = client.get("/api/help")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["title"] == "LibreOffice MCP"
    assert "fleet-report.odt" in body["templates"]


def test_api_capabilities(client: TestClient):
    r = client.get("/api/capabilities")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["tool_surface"]["portmanteau"] == "libreoffice"
    assert body["features"]["openapi_docs"] is True
    assert body["features"]["simple_actions"] is True
    assert body["features"]["skills"] is True
    assert body["features"]["prefab_apps"] is True
    assert body["features"]["sampling"] is True
    assert body["features"]["webapp_tests"] is True
    assert body["features"]["file_upload"] is True
    assert body["tool_surface"]["operation_count"] >= 14


def test_api_logs(client: TestClient):
    r = client.get("/api/logs")
    assert r.status_code == 200
    assert "logs" in r.json()


def test_api_fleet_apps(client: TestClient):
    r = client.get("/api/fleet/apps")
    assert r.status_code == 200
    body = r.json()
    assert "apps" in body
    assert isinstance(body["apps"], list)


def test_api_env(client: TestClient):
    r = client.get("/api/env")
    assert r.status_code == 200
    body = r.json()
    assert "LIBREOFFICE_MCP_EXTENSION_BRIDGE_URL" in body


def test_api_llm_discover(client: TestClient):
    r = client.get("/api/llm/discover")
    assert r.status_code == 200
    body = r.json()
    assert "providers" in body
    assert len(body["providers"]) >= 1


def test_api_templates(client: TestClient):
    r = client.get("/api/templates")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    names = {t["name"] for t in body["templates"]}
    assert "fleet-report.odt" in names
    assert "fleet-board-pack.odt" in names
    assert "fleet-artifact-pack.odt" in names


def test_api_jobs_empty(client: TestClient):
    r = client.get("/api/jobs")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["jobs"] == []


def test_api_output_empty(client: TestClient):
    r = client.get("/api/output")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["files"] == []


def test_api_convert_missing_file(client: TestClient):
    r = client.post(
        "/api/convert", json={"input_path": "C:/no/such/file.md", "output_format": "pdf"}
    )
    assert r.status_code == 400


def test_api_merge(client: TestClient, tmp_path):
    r = client.post(
        "/api/merge",
        json={
            "template": "fleet-report.odt",
            "placeholders": {
                "TITLE": "API Test",
                "DATE": "2026-05-30",
                "SUMMARY": "ok",
                "BODY": "body",
            },
            "output_format": "odt",
            "output_stem": "api-merge-test",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    out = Path(body["data"]["output"])
    assert out.is_file()


def test_api_output_file_invalid_name(client: TestClient):
    r = client.get("/api/output/file/../secrets")
    assert r.status_code in {400, 404}


def test_api_actions_catalog(client: TestClient):
    r = client.get("/api/actions")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    ids = {a["id"] for a in body["simple_actions"]}
    assert "status" in ids
    assert "convert" in ids


def test_api_workflows_catalog(client: TestClient):
    r = client.get("/api/workflows")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    ids = {w["id"] for w in body["workflows"]}
    assert "coworker_weekly_report_pdf" in ids
    assert "batch_markdown_pack" in ids


def test_api_agentic_plan(client: TestClient):
    r = client.post(
        "/api/agentic", json={"goal": "check bridge and list templates", "execute": False}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert len(body["steps"]) >= 1


def test_api_run_action_status(client: TestClient):
    r = client.post("/api/actions/run", json={"action_id": "status", "params": {}})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert "data" in body


def test_api_skills(client: TestClient):
    r = client.get("/api/skills")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    ids = {s["id"] for s in body["skills"]}
    assert "libreoffice-expert" in ids


def test_api_tools_includes_agentic(client: TestClient):
    r = client.get("/api/tools")
    names = {t["name"] for t in r.json()["tools"]}
    assert "libreoffice_agentic_workflow" in names
    assert "show_libreoffice_status_card" in names


def test_api_formats(client: TestClient):
    r = client.get("/api/formats")
    assert r.status_code == 200
    body = r.json()
    assert "writer" in body
    assert "pdf" in body["writer"]


def test_api_tests_run(client: TestClient):
    r = client.get("/api/tests/run?include_soffice=false")
    assert r.status_code == 200
    body = r.json()
    assert "results" in body
    assert body["total"] >= 3


def test_api_chat_plan(client: TestClient):
    r = client.post("/api/chat", json={"message": "convert report.pdf to docx", "execute": False})
    assert r.status_code == 200
    body = r.json()
    assert body["role"] == "assistant"
    assert "content" in body
