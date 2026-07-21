"""Headless LibreOffice conversion via soffice CLI."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .config import settings
from .formats import detect_family, suggested_formats
from .markdown_html import markdown_to_html


def find_soffice() -> Path | None:
    return settings.resolve_soffice()


def _prepare_input(input_path: Path, target_dir: Path) -> tuple[Path, Path | None]:
    """Return path to convert and optional temp file to delete after."""
    ext = input_path.suffix.lower()
    if ext not in {".md", ".markdown"}:
        return input_path, None

    html_path = target_dir / f"{input_path.stem}-report.html"
    title = input_path.stem.replace("-", " ").title()
    html_path.write_text(
        markdown_to_html(input_path.read_text(encoding="utf-8"), title=title),
        encoding="utf-8",
    )
    return html_path, html_path


def _soffice_error(proc: subprocess.CompletedProcess[str]) -> str:
    stderr = (proc.stderr or "").strip()
    stdout = (proc.stdout or "").strip()
    parts = [p for p in (stderr, stdout) if p]
    msg = " | ".join(parts) if parts else "soffice exited with non-zero status"
    return f"{msg} (exit {proc.returncode})"


def convert_file(
    input_path: Path,
    output_format: str,
    *,
    outdir: Path | None = None,
) -> dict[str, Any]:
    """Convert a document using `soffice --headless --convert-to`."""
    soffice = find_soffice()
    if soffice is None:
        return {
            "success": False,
            "error": "LibreOffice soffice not found. Set LIBREOFFICE_MCP_SOFFICE_PATH.",
            "hint": "Install LibreOffice — see INSTALL.md",
        }

    src = Path(input_path)
    if not src.is_file():
        return {"success": False, "error": f"Input not found: {src}"}

    family = detect_family(src)
    target_dir = outdir or settings.output_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    convert_src, temp_html = _prepare_input(src, target_dir)

    cmd = [
        str(soffice),
        "--headless",
        "--norestore",
        "--invisible",
        "--convert-to",
        output_format,
        "--outdir",
        str(target_dir),
        str(convert_src.resolve()),
    ]

    proc = None
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=settings.convert_timeout_sec,
            check=False,
        )
    except subprocess.TimeoutExpired:
        if temp_html and temp_html.is_file():
            temp_html.unlink(missing_ok=True)
        return {
            "success": False,
            "error": f"Conversion timed out after {settings.convert_timeout_sec}s",
            "input": str(src),
            "family": family,
        }
    except OSError as exc:
        if temp_html and temp_html.is_file():
            temp_html.unlink(missing_ok=True)
        return {"success": False, "error": str(exc), "input": str(src)}
    finally:
        if temp_html and temp_html.is_file():
            temp_html.unlink(missing_ok=True)

    if proc is None or proc.returncode != 0:
        return {
            "success": False,
            "error": _soffice_error(proc) if proc else "soffice failed",
            "returncode": proc.returncode if proc else -1,
            "input": str(src),
            "family": family,
            "suggested_formats": suggested_formats(src),
            "command": " ".join(cmd[:6]) + " ...",
        }

    ext = output_format.split(":")[0]
    stem = convert_src.stem
    expected = target_dir / f"{stem}.{ext}"
    if not expected.is_file():
        expected = target_dir / f"{src.stem}.{ext}"
    if not expected.is_file():
        produced = sorted(
            target_dir.glob(f"{stem}.*"), key=lambda p: p.stat().st_mtime, reverse=True
        )
        if not produced:
            produced = sorted(
                target_dir.glob(f"{src.stem}.*"), key=lambda p: p.stat().st_mtime, reverse=True
            )
        expected = produced[0] if produced else expected

    ok = expected.is_file()
    return {
        "success": ok,
        "input": str(src),
        "output": str(expected) if ok else None,
        "format": output_format,
        "family": family,
        "message": (proc.stdout or "").strip() or "converted",
        "error": None if ok else f"Expected output missing: {expected.name}",
    }


def convert_batch(
    input_paths: list[Path],
    output_format: str,
    *,
    outdir: Path | None = None,
) -> dict[str, Any]:
    """Convert multiple files; continues on individual failures."""
    results: list[dict[str, Any]] = []
    for path in input_paths:
        results.append(convert_file(path, output_format, outdir=outdir))
    ok_count = sum(1 for r in results if r.get("success"))
    return {
        "success": ok_count > 0,
        "count": len(results),
        "ok_count": ok_count,
        "results": results,
        "message": f"Converted {ok_count}/{len(results)} files",
    }
