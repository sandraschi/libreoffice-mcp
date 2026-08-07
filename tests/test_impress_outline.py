"""Tests for impress outline to ODP builder."""

from __future__ import annotations

import zipfile

from libreoffice_mcp.impress_outline import (
    outline_to_odp,
    parse_markdown_outline,
    write_odp,
)

SAMPLE = """# Fleet Update
## Status
- All green
- Studio live
## Next
- Email concierge
"""


def test_parse_markdown_outline():
    title, slides = parse_markdown_outline(SAMPLE)
    assert title == "Fleet Update"
    assert len(slides) == 2
    assert slides[0].title == "Status"
    assert slides[0].bullets[0] == "All green"


def test_write_odp_creates_zip(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "libreoffice_mcp.impress_outline.find_soffice",
        lambda: tmp_path / "soffice.exe",
    )
    title, slides = parse_markdown_outline(SAMPLE)
    out = tmp_path / "deck.odp"
    write_odp(title, slides, out)
    assert out.is_file()
    with zipfile.ZipFile(out) as zf:
        names = set(zf.namelist())
    assert "content.xml" in names
    assert "mimetype" in names


def test_outline_to_odp(monkeypatch, tmp_path):
    fake_soffice = tmp_path / "soffice.exe"
    fake_soffice.write_text("stub", encoding="utf-8")
    monkeypatch.setattr("libreoffice_mcp.impress_outline.find_soffice", lambda: fake_soffice)
    monkeypatch.setattr(
        "libreoffice_mcp.impress_outline.settings.output_dir",
        tmp_path,
    )
    result = outline_to_odp(SAMPLE, open_in_impress=False)
    assert result["success"] is True
    assert result["slide_count"] == 2
    assert (tmp_path / result["filename"]).is_file()
