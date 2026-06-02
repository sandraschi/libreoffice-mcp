"""Tests for ODT template merge."""

from pathlib import Path

from libreoffice_mcp.templates import (
    ensure_builtin_templates,
    list_templates,
    merge_odt_template,
)


def test_ensure_builtin_templates(tmp_path, monkeypatch):
    from libreoffice_mcp import config

    monkeypatch.setattr(config.settings, "templates_dir", tmp_path / "templates")
    monkeypatch.setattr(config.settings, "output_dir", tmp_path / "output")

    created = ensure_builtin_templates()
    assert "fleet-report.odt" in created
    assert (tmp_path / "templates" / "fleet-report.odt").is_file()

    again = ensure_builtin_templates()
    assert again == []


def test_merge_odt_placeholders(tmp_path, monkeypatch):
    from libreoffice_mcp import config

    templates_dir = tmp_path / "templates"
    output_dir = tmp_path / "output"
    monkeypatch.setattr(config.settings, "templates_dir", templates_dir)
    monkeypatch.setattr(config.settings, "output_dir", output_dir)

    ensure_builtin_templates()
    template = templates_dir / "fleet-report.odt"
    result = merge_odt_template(
        template,
        {
            "TITLE": "Test Report",
            "DATE": "2026-05-30",
            "SUMMARY": "All green",
            "BODY": "Line one\nLine two",
        },
        output_stem="test-report",
    )
    assert result["success"] is True
    merged = Path(result["output"])
    assert merged.is_file()
    assert merged.suffix == ".odt"


def test_list_templates_includes_builtins(tmp_path, monkeypatch):
    from libreoffice_mcp import config

    monkeypatch.setattr(config.settings, "templates_dir", tmp_path / "templates")
    monkeypatch.setattr(config.settings, "output_dir", tmp_path / "output")

    rows = list_templates()
    names = {row["name"] for row in rows}
    assert "fleet-board-pack.odt" in names
    assert "fleet-artifact-pack.odt" in names
