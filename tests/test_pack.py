"""Tests for batch markdown pack."""

from pathlib import Path

from libreoffice_mcp.pack import pack_markdown_files


def test_pack_markdown_md_only(tmp_path, monkeypatch):
    from libreoffice_mcp import config

    monkeypatch.setattr(config.settings, "output_dir", tmp_path / "output")

    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text("# A\n\nline", encoding="utf-8")
    b.write_text("# B\n\nline", encoding="utf-8")

    result = pack_markdown_files([a, b], title="Pack", output_stem="test-pack", output_format="md")
    assert result["success"] is True
    assert result["count"] == 2
    assert Path(result["output"]).is_file()
    text = Path(result["output"]).read_text(encoding="utf-8")
    assert "a.md" in text
    assert "b.md" in text
