"""Batch markdown → single PDF pack."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .config import settings
from .headless import convert_file
from .markdown_html import markdown_to_html
from .templates import markdown_to_plain_body


def pack_markdown_files(
    paths: list[Path],
    *,
    title: str,
    output_stem: str,
    output_format: str = "pdf",
) -> dict[str, Any]:
    """Combine multiple markdown files into one document and convert."""
    sources = [Path(p) for p in paths if Path(p).is_file()]
    if not sources:
        return {"success": False, "error": "No readable markdown files provided"}

    sections: list[str] = [f"# {title}", ""]
    for path in sources:
        sections.extend(
            [
                f"## {path.name}",
                "",
                path.read_text(encoding="utf-8", errors="replace").strip(),
                "",
                "---",
                "",
            ]
        )
    combined_md = "\n".join(sections).strip()

    settings.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(ZoneInfo("UTC")).strftime("%Y%m%d")
    stem = output_stem or f"artifact-pack-{stamp}"
    md_path = settings.output_dir / f"{stem}.md"
    md_path.write_text(combined_md, encoding="utf-8")

    if output_format.lower() == "md":
        return {
            "success": True,
            "output": str(md_path),
            "format": "md",
            "sources": [str(p) for p in sources],
            "count": len(sources),
        }

    if output_format.lower() in {"html", "htm"}:
        html_path = settings.output_dir / f"{stem}.html"
        html_path.write_text(markdown_to_html(combined_md, title=title), encoding="utf-8")
        return {
            "success": True,
            "output": str(html_path),
            "format": "html",
            "sources": [str(p) for p in sources],
            "count": len(sources),
        }

    converted = convert_file(md_path, output_format)
    if not converted.get("success"):
        return {
            "success": False,
            "error": converted.get("error", "batch convert failed"),
            "combined_md": str(md_path),
            "sources": [str(p) for p in sources],
        }

    if converted.get("output"):
        from .storage import index_output

        index_output(Path(converted["output"]), fmt=output_format)

    return {
        "success": True,
        "output": converted.get("output"),
        "format": output_format,
        "combined_md": str(md_path),
        "sources": [str(p) for p in sources],
        "count": len(sources),
        "convert": converted,
    }


def pack_markdown_plain_summary(paths: list[Path], *, max_chars: int = 12000) -> str:
    """Plain-text body for ODT merge templates."""
    chunks: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        chunks.append(f"=== {path.name} ===")
        chunks.append(markdown_to_plain_body(path.read_text(encoding="utf-8", errors="replace")))
        chunks.append("")
    text = "\n".join(chunks).strip()
    if len(text) > max_chars:
        return text[: max_chars - 3] + "..."
    return text
