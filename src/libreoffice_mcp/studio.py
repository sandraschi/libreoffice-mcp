"""Live Studio session snapshot for the webapp hub."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .calc_session import calc_session_connected
from .config import settings
from .headless import find_soffice
from .live_session import writer_session_connected
from .storage import list_indexed_outputs


def _recent_outputs(limit: int = 10) -> list[dict[str, Any]]:
    indexed = list_indexed_outputs(limit=limit)
    if indexed:
        return indexed

    out = settings.output_dir
    if not out.is_dir():
        return []

    files: list[dict[str, Any]] = []
    for path in sorted(out.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
        if not path.is_file():
            continue
        stat = path.stat()
        ext = path.suffix.lower()
        files.append(
            {
                "name": path.name,
                "path": str(path),
                "size_bytes": stat.st_size,
                "format": ext.lstrip(".") or None,
                "previewable": ext in {".pdf", ".html", ".htm"},
            }
        )
    return files


def build_studio_session() -> dict[str, Any]:
    """Aggregate Live Studio hub state for GET /api/studio/session."""
    soffice = find_soffice()
    return {
        "soffice_available": soffice is not None,
        "soffice_path": str(soffice) if soffice else None,
        "writer_bridge_connected": writer_session_connected(),
        "calc_bridge_connected": calc_session_connected(),
        "output_dir": str(settings.output_dir),
        "live_pages": {
            "studio": "/studio",
            "live_write": "/live-write",
            "live_calc": "/live-calc",
        },
        "recent_outputs": _recent_outputs(),
    }


def resolve_output_path(name: str) -> Path:
    """Resolve a filename within the configured output directory."""
    if not name or name != Path(name).name or ".." in name:
        raise ValueError("Invalid filename")
    path = (settings.output_dir / name).resolve()
    output_root = settings.output_dir.resolve()
    if output_root not in path.parents and path != output_root:
        raise ValueError("Path outside output directory")
    if not path.is_file():
        raise ValueError(f"File not found: {name}")
    return path
