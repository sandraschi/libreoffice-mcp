"""Tests for document family detection."""

from pathlib import Path

from libreoffice_mcp.formats import detect_family, document_info, suggested_formats


def test_detect_writer():
    assert detect_family(Path("report.docx")) == "writer"
    assert detect_family(Path("notes.md")) == "writer"


def test_detect_calc():
    assert detect_family(Path("data.xlsx")) == "calc"


def test_detect_impress():
    assert detect_family(Path("deck.pptx")) == "impress"


def test_suggested_formats_calc():
    fmts = suggested_formats(Path("sheet.ods"))
    assert "xlsx" in fmts
    assert "pdf" in fmts


def test_document_info_missing():
    info = document_info(Path("/no/such/file.odt"))
    assert info["success"] is False
