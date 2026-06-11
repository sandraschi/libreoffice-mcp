"""Headless spreadsheet read — adapted from mcp-libre (see external/mcp-libre, MIT)."""

from __future__ import annotations

import csv
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .config import settings
from .headless import find_soffice


def read_spreadsheet_data(
    path: Path,
    *,
    sheet_name: str | None = None,
    max_rows: int = 100,
) -> dict[str, Any]:
    """Convert sheet to CSV via soffice, return rows as list[list[str]]."""
    src = Path(path)
    if not src.is_file():
        return {"success": False, "error": f"Not found: {src}"}

    soffice = find_soffice()
    if soffice is None:
        return {"success": False, "error": "soffice not found"}

    try:
        with tempfile.TemporaryDirectory(prefix="lo-mcp-csv-") as tmp:
            tmp_path = Path(tmp)
            proc = subprocess.run(
                [
                    str(soffice),
                    "--headless",
                    "--norestore",
                    "--convert-to",
                    "csv",
                    "--outdir",
                    str(tmp_path),
                    str(src.resolve()),
                ],
                capture_output=True,
                text=True,
                timeout=settings.convert_timeout_sec,
                check=False,
            )
            if proc.returncode != 0:
                return {
                    "success": False,
                    "error": (proc.stderr or proc.stdout or "csv convert failed")[:500],
                }
            csv_file = tmp_path / f"{src.stem}.csv"
            if not csv_file.is_file():
                candidates = list(tmp_path.glob("*.csv"))
                csv_file = candidates[0] if candidates else csv_file
            if not csv_file.is_file():
                return {"success": False, "error": "CSV output missing after convert"}

            rows: list[list[str]] = []
            with csv_file.open(encoding="utf-8", newline="") as fh:
                for i, row in enumerate(csv.reader(fh)):
                    if i >= max_rows:
                        break
                    rows.append(row)

            col_count = max((len(r) for r in rows), default=0)
            return {
                "success": True,
                "path": str(src.resolve()),
                "sheet_name": sheet_name or "Sheet1",
                "data": rows,
                "row_count": len(rows),
                "col_count": col_count,
                "source": "mcp-libre-pattern-headless-csv",
            }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "CSV conversion timed out"}
    except OSError as exc:
        return {"success": False, "error": str(exc)}
