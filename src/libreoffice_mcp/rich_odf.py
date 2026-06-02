"""Markdown → ODF XML fragments for rich template placeholders."""

from __future__ import annotations

import html
import re

_LIST_ITEM = re.compile(r"^(\s*)[-*]\s+(.*)$")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITALIC = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")

RICH_PLACEHOLDER_KEYS = frozenset(
    {"BODY", "NARRATIVE", "KPI_TABLE", "ACTION_ITEMS", "SUMMARY", "CONTENT", "NOTES"}
)


def _inline_odf(text: str) -> str:
    """Escape and apply minimal inline markdown (bold/italic) as ODF spans."""
    escaped = html.escape(text)
    escaped = _BOLD.sub(r'<text:span text:style-name="Bold">\1</text:span>', escaped)
    escaped = _ITALIC.sub(r'<text:span text:style-name="Emphasis">\1</text:span>', escaped)
    return escaped


def markdown_to_odf_xml(text: str) -> str:
    """Convert markdown body to ODF text XML (paragraphs, headings, lists)."""
    lines = text.replace("\r\n", "\n").split("\n")
    parts: list[str] = []
    in_list = False

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            parts.append("</text:list>")
            in_list = False

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            close_list()
            continue

        if stripped.startswith("### "):
            close_list()
            parts.append(f'<text:h text:outline-level="3">{_inline_odf(stripped[4:])}</text:h>')
            continue
        if stripped.startswith("## "):
            close_list()
            parts.append(f'<text:h text:outline-level="2">{_inline_odf(stripped[3:])}</text:h>')
            continue
        if stripped.startswith("# "):
            close_list()
            parts.append(f'<text:h text:outline-level="1">{_inline_odf(stripped[2:])}</text:h>')
            continue

        list_match = _LIST_ITEM.match(line)
        if list_match:
            if not in_list:
                parts.append('<text:list text:style-name="List">')
                in_list = True
            parts.append(
                f"<text:list-item><text:p>{_inline_odf(list_match.group(2))}</text:p></text:list-item>"
            )
            continue

        close_list()
        parts.append(f'<text:p text:style-name="BodyText">{_inline_odf(stripped)}</text:p>')

    close_list()
    return "".join(parts)


def is_rich_placeholder(key: str, value: str) -> bool:
    if key in RICH_PLACEHOLDER_KEYS and len(value) > 80:
        return True
    if key in RICH_PLACEHOLDER_KEYS and any(
        marker in value for marker in ("##", "**", "\n- ", "\n* ")
    ):
        return True
    return False
