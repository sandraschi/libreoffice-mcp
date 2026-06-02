"""SQLite persistence for jobs and output file index."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    input TEXT,
    output_format TEXT,
    started TEXT NOT NULL,
    finished TEXT,
    result_json TEXT,
    error TEXT,
    kind TEXT DEFAULT 'convert'
);
CREATE TABLE IF NOT EXISTS outputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    format TEXT,
    job_id TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_jobs_started ON jobs(started DESC);
CREATE INDEX IF NOT EXISTS idx_outputs_created ON outputs(created_at DESC);
"""


def db_path() -> Path:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings.data_dir / "libreoffice-mcp.db"


@contextmanager
def _conn() -> Iterator[sqlite3.Connection]:
    path = db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(_SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def _row_to_job(row: sqlite3.Row) -> dict[str, Any]:
    job: dict[str, Any] = {
        "id": row["id"],
        "name": row["name"],
        "status": row["status"],
        "input": row["input"],
        "output_format": row["output_format"],
        "started": row["started"],
        "finished": row["finished"],
        "result": json.loads(row["result_json"]) if row["result_json"] else None,
        "error": row["error"],
        "kind": row["kind"] or "convert",
    }
    return job


def save_job(job: dict[str, Any]) -> None:
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO jobs (id, name, status, input, output_format, started, finished, result_json, error, kind)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name, status=excluded.status, input=excluded.input,
                output_format=excluded.output_format, finished=excluded.finished,
                result_json=excluded.result_json, error=excluded.error, kind=excluded.kind
            """,
            (
                job["id"],
                job["name"],
                job["status"],
                job.get("input"),
                job.get("output_format"),
                job["started"],
                job.get("finished"),
                json.dumps(job["result"]) if job.get("result") is not None else None,
                job.get("error"),
                job.get("kind", "convert"),
            ),
        )


def list_jobs(limit: int = 50) -> list[dict[str, Any]]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM jobs ORDER BY started DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [_row_to_job(r) for r in rows]


def get_job(job_id: str) -> dict[str, Any] | None:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return _row_to_job(row) if row else None


def index_output(
    path: Path,
    *,
    fmt: str | None = None,
    job_id: str | None = None,
) -> dict[str, Any]:
    if not path.is_file():
        return {"success": False, "error": f"Not a file: {path}"}
    stat = path.stat()
    created = datetime.now(UTC).isoformat()
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO outputs (path, name, size_bytes, format, job_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                size_bytes=excluded.size_bytes, format=excluded.format,
                job_id=excluded.job_id, created_at=excluded.created_at
            """,
            (str(path.resolve()), path.name, stat.st_size, fmt, job_id, created),
        )
    return {
        "success": True,
        "path": str(path.resolve()),
        "name": path.name,
        "size_bytes": stat.st_size,
        "format": fmt,
        "job_id": job_id,
    }


def list_indexed_outputs(limit: int = 50) -> list[dict[str, Any]]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM outputs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {
            "name": r["name"],
            "path": r["path"],
            "size_bytes": r["size_bytes"],
            "format": r["format"],
            "job_id": r["job_id"],
            "created_at": r["created_at"],
            "previewable": Path(r["name"]).suffix.lower() in {".pdf", ".html", ".htm"},
        }
        for r in rows
    ]
