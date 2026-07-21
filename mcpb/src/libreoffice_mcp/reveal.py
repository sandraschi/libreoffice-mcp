"""Reveal output files in the system file manager."""

from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path
from typing import Any


def reveal_path(path: Path) -> dict[str, Any]:
    """Open folder and select file (Windows/macOS/Linux best-effort)."""
    p = Path(path).resolve()
    if not p.exists():
        return {"success": False, "error": f"Path not found: {p}"}

    system = platform.system()
    try:
        if system == "Windows":
            if p.is_file():
                subprocess.run(
                    ["explorer", "/select,", str(p)],
                    check=False,
                )
            else:
                os.startfile(str(p))  # noqa: S606
        elif system == "Darwin":
            args = ["open", "-R", str(p)] if p.is_file() else ["open", str(p)]
            subprocess.run(args, check=False)
        else:
            folder = str(p.parent if p.is_file() else p)
            subprocess.run(["xdg-open", folder], check=False)
    except OSError as exc:
        return {"success": False, "error": str(exc)}

    return {"success": True, "path": str(p), "message": "Opened in file manager"}
