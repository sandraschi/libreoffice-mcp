"""Tests for markdown → HTML conversion."""

from libreoffice_mcp.markdown_html import markdown_to_html


def test_markdown_to_html_headings_and_list():
    md = "# Title\n\n## Section\n\n- item one\n- `code` item\n"
    html = markdown_to_html(md, title="Test")
    assert "<h1>Title</h1>" in html
    assert "<h2>Section</h2>" in html
    assert "<li>item one</li>" in html
    assert "<code>code</code>" in html
    assert "<title>Test</title>" in html
