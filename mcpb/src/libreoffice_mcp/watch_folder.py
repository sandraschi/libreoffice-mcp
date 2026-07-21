"""Watch a folder and auto-convert new/changed documents."""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

from .config import settings
from .headless import convert_file
from .storage import index_output

log = logging.getLogger(__name__)

_state: dict[str, Any] = {
    "running": False,
    "watch_path": None,
    "glob": "*.*",
    "output_format": "pdf",
    "processed": 0,
    "last_error": None,
    "thread": None,
    "stop_event": None,
    "seen_mtimes": {},
}


def watch_status() -> dict[str, Any]:
    return {
        "running": _state["running"],
        "watch_path": _state["watch_path"],
        "glob": _state["glob"],
        "output_format": _state["output_format"],
        "processed": _state["processed"],
        "last_error": _state["last_error"],
    }


def _watch_loop(
    watch_path: Path,
    glob_pattern: str,
    output_format: str,
    stop_event: threading.Event,
) -> None:
    while not stop_event.is_set():
        try:
            for path in watch_path.glob(glob_pattern):
                if not path.is_file():
                    continue
                if path.suffix.lower() in {".tmp", ".partial", ".db"}:
                    continue
                mtime = path.stat().st_mtime
                key = str(path.resolve())
                prev = _state["seen_mtimes"].get(key)
                if prev is not None and mtime <= prev:
                    continue
                result = convert_file(path, output_format)
                _state["seen_mtimes"][key] = mtime
                if result.get("success") and result.get("output"):
                    index_output(Path(result["output"]), fmt=output_format)
                    _state["processed"] += 1
                    _state["last_error"] = None
                    log.info("Watch converted %s → %s", path.name, result["output"])
                elif not result.get("success"):
                    _state["last_error"] = result.get("error")
        except OSError as exc:
            _state["last_error"] = str(exc)
        stop_event.wait(settings.watch_poll_sec)


def start_watch(
    watch_path: str | Path,
    *,
    glob_pattern: str = "*.*",
    output_format: str = "pdf",
) -> dict[str, Any]:
    path = Path(watch_path)
    if not path.is_dir():
        return {"success": False, "error": f"Watch path not found: {path}"}

    stop_watch()

    stop_event = threading.Event()
    thread = threading.Thread(
        target=_watch_loop,
        args=(path, glob_pattern, output_format, stop_event),
        daemon=True,
        name="libreoffice-mcp-watch",
    )
    _state.update(
        {
            "running": True,
            "watch_path": str(path.resolve()),
            "glob": glob_pattern,
            "output_format": output_format,
            "processed": 0,
            "last_error": None,
            "stop_event": stop_event,
            "thread": thread,
            "seen_mtimes": {},
        }
    )
    thread.start()
    return {"success": True, **watch_status(), "message": f"Watching {path}"}


def stop_watch() -> dict[str, Any]:
    if _state.get("stop_event"):
        _state["stop_event"].set()
    if _state.get("thread"):
        _state["thread"].join(timeout=2.0)
    _state["running"] = False
    _state["thread"] = None
    _state["stop_event"] = None
    return {"success": True, **watch_status(), "message": "Watch stopped"}
