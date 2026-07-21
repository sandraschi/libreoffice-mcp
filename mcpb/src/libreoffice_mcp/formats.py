"""Document family detection and supported conversion formats."""

from __future__ import annotations

from pathlib import Path

WRITER_EXTS = {
    ".odt",
    ".doc",
    ".docx",
    ".rtf",
    ".txt",
    ".md",
    ".html",
    ".htm",
    ".pdf",
}
CALC_EXTS = {".ods", ".xls", ".xlsx", ".csv", ".tsv"}
IMPRESS_EXTS = {".odp", ".ppt", ".pptx"}
DRAW_EXTS = {".odg", ".svg"}

WRITER_OUTPUT = ["pdf", "docx", "odt", "html", "txt", "rtf"]
CALC_OUTPUT = ["pdf", "xlsx", "ods", "csv", "html"]
IMPRESS_OUTPUT = ["pdf", "pptx", "odp", "html"]

FAMILY_LABELS = {
    "writer": "Writer (text documents)",
    "calc": "Calc (spreadsheets)",
    "impress": "Impress (presentations)",
    "draw": "Draw (vector graphics)",
    "unknown": "Unknown / generic",
}


def detect_family(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in WRITER_EXTS:
        return "writer"
    if ext in CALC_EXTS:
        return "calc"
    if ext in IMPRESS_EXTS:
        return "impress"
    if ext in DRAW_EXTS:
        return "draw"
    return "unknown"


def suggested_formats(path: Path) -> list[str]:
    family = detect_family(path)
    if family == "writer":
        return WRITER_OUTPUT
    if family == "calc":
        return CALC_OUTPUT
    if family == "impress":
        return IMPRESS_OUTPUT
    return ["pdf", "html", "odt", "docx", "xlsx", "pptx"]


def document_info(path: Path) -> dict[str, object]:
    p = Path(path)
    if not p.is_file():
        return {"success": False, "error": f"Not a file: {p}"}
    family = detect_family(p)
    stat = p.stat()
    return {
        "success": True,
        "path": str(p.resolve()),
        "name": p.name,
        "extension": p.suffix.lower(),
        "family": family,
        "family_label": FAMILY_LABELS.get(family, family),
        "size_bytes": stat.st_size,
        "suggested_formats": suggested_formats(p),
    }
