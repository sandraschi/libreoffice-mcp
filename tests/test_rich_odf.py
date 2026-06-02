"""Tests for markdown → ODF rich placeholders."""

from libreoffice_mcp.rich_odf import is_rich_placeholder, markdown_to_odf_xml


def test_markdown_to_odf_headings():
    xml = markdown_to_odf_xml("# Title\n\nParagraph **bold**.")
    assert "text:h" in xml
    assert "Bold" in xml or "bold" in xml.lower()
    assert "text:p" in xml


def test_is_rich_placeholder():
    assert is_rich_placeholder("BODY", "## Section\n\nContent")
    assert not is_rich_placeholder("DATE", "2026-05-30")
