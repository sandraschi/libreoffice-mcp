"""Minimal markdown → HTML for headless Writer PDF export."""

from __future__ import annotations

import html
import re

_LIST_ITEM = re.compile(r"^(\s*)[-*]\s+(.*)$")


def markdown_to_html(text: str, *, title: str = "Report") -> str:
    """Convert coworker-style markdown to a simple HTML document."""
    lines = text.splitlines()
    parts: list[str] = []
    in_list = False

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            parts.append("</ul>")
            in_list = False

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        if not stripped:
            close_list()
            continue

        if stripped.startswith("### "):
            close_list()
            parts.append(f"<h3>{html.escape(stripped[4:])}</h3>")
            continue
        if stripped.startswith("## "):
            close_list()
            parts.append(f"<h2>{html.escape(stripped[3:])}</h2>")
            continue
        if stripped.startswith("# "):
            close_list()
            parts.append(f"<h1>{html.escape(stripped[2:])}</h1>")
            continue

        list_match = _LIST_ITEM.match(line)
        if list_match:
            body = list_match.group(2).strip()
            body = re.sub(
                r"`([^`]+)`",
                lambda m: f"<code>{html.escape(m.group(1))}</code>",
                html.escape(body),
            )
            if not in_list:
                parts.append("<ul>")
                in_list = True
            parts.append(f"<li>{body}</li>")
            continue

        close_list()
        if "`" in stripped:
            escaped = html.escape(stripped)
            escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
            parts.append(f"<p>{escaped}</p>")
        else:
            parts.append(f"<p>{html.escape(stripped)}</p>")

    close_list()
    body = "\n".join(parts)
    safe_title = html.escape(title)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>{safe_title}</title>
  <style>
    body {{ font-family: Liberation Sans, Arial, sans-serif; margin: 2cm; line-height: 1.45; color: #1a1a1a; }}
    h1 {{ font-size: 1.6rem; border-bottom: 2px solid #333; padding-bottom: 0.3rem; }}
    h2 {{ font-size: 1.25rem; margin-top: 1.2rem; }}
    h3 {{ font-size: 1.05rem; margin-top: 0.8rem; }}
    code {{ background: #f4f4f4; padding: 0.1rem 0.35rem; border-radius: 3px; font-size: 0.92em; }}
    ul {{ padding-left: 1.4rem; }}
    li {{ margin: 0.25rem 0; }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""
