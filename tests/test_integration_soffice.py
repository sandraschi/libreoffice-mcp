"""Integration tests requiring live LibreOffice soffice."""

from __future__ import annotations

from pathlib import Path

import pytest

from libreoffice_mcp.headless import convert_file, find_soffice

pytestmark = pytest.mark.skipif(
    find_soffice() is None,
    reason="LibreOffice soffice not installed",
)


def test_convert_markdown_to_pdf(tmp_path):
    md = tmp_path / "sample.md"
    md.write_text("# Integration Test\n\nHello from pytest.\n", encoding="utf-8")
    outdir = tmp_path / "out"
    outdir.mkdir()
    result = convert_file(md, "pdf", outdir=outdir)
    assert result.get("success"), result.get("error")
    assert result.get("output")
    assert Path(result["output"]).is_file()
    assert Path(result["output"]).stat().st_size > 500
