"""PDF merge and manipulation via pypdf."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import settings


def merge_pdfs(
    input_paths: list[Path],
    *,
    output_stem: str = "merged",
) -> dict[str, Any]:
    try:
        from pypdf import PdfWriter
    except ImportError:
        return {
            "success": False,
            "error": "pypdf not installed — run uv sync",
        }

    sources = [Path(p) for p in input_paths if Path(p).is_file()]
    if len(sources) < 1:
        return {"success": False, "error": "At least one PDF path required"}

    bad = [str(p) for p in sources if p.suffix.lower() != ".pdf"]
    if bad:
        return {"success": False, "error": f"Not PDF files: {', '.join(bad[:5])}"}

    settings.output_dir.mkdir(parents=True, exist_ok=True)
    out_path = settings.output_dir / f"{output_stem}.pdf"

    writer = PdfWriter()
    try:
        for src in sources:
            writer.append(str(src))
        with out_path.open("wb") as fh:
            writer.write(fh)
    except Exception as exc:
        return {"success": False, "error": f"PDF merge failed: {exc}"}
    finally:
        writer.close()

    return {
        "success": True,
        "output": str(out_path),
        "format": "pdf",
        "count": len(sources),
        "sources": [str(p) for p in sources],
    }
