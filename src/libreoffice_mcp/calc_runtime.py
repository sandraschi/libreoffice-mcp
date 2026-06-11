"""Execute Calc actions via live .oxt bridge."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .calc_session import queue_calc_action
from .headless import find_soffice


async def execute_calc_action(
    action: dict[str, Any],
    *,
    timeout: float = 90.0,
) -> dict[str, Any]:
    return await queue_calc_action(action, timeout=timeout)


def launch_calc_gui(*, document_path: Path | None = None) -> dict[str, Any]:
    soffice = find_soffice()
    if soffice is None:
        return {"success": False, "error": "soffice not found"}
    cmd = [str(soffice), "--calc"]
    if document_path and document_path.is_file():
        cmd.append(str(document_path))
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {
            "success": True,
            "message": "Calc launched",
            "path": str(document_path) if document_path else None,
        }
    except OSError as exc:
        return {"success": False, "error": str(exc)}
