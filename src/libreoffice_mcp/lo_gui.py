"""Launch LibreOffice GUI apps (Writer, Calc, Impress, Draw)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Literal

from .headless import find_soffice

LoFamily = Literal["writer", "calc", "impress", "draw"]

_FAMILY_FLAGS: dict[LoFamily, str] = {
    "writer": "--writer",
    "calc": "--calc",
    "impress": "--impress",
    "draw": "--draw",
}


def launch_lo_gui(
    family: LoFamily,
    document_path: Path | None = None,
) -> dict[str, Any]:
    """Open a LibreOffice GUI module, optionally with a document."""
    if family not in _FAMILY_FLAGS:
        return {"success": False, "error": f"Unknown family: {family}"}

    soffice = find_soffice()
    if soffice is None:
        return {"success": False, "error": "soffice not found"}

    cmd = [str(soffice), _FAMILY_FLAGS[family]]
    if document_path and document_path.is_file():
        cmd.append(str(document_path))

    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {
            "success": True,
            "message": f"{family.title()} launched",
            "family": family,
            "path": str(document_path) if document_path else None,
        }
    except OSError as exc:
        return {"success": False, "error": str(exc)}
