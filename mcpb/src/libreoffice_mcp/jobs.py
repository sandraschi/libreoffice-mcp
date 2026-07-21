"""Persistent convert job queue backed by SQLite."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .headless import convert_file
from .storage import get_job as db_get_job
from .storage import index_output, save_job
from .storage import list_jobs as db_list_jobs

_tasks: set[asyncio.Task] = set()


def list_jobs(limit: int = 50) -> list[dict[str, Any]]:
    return db_list_jobs(limit)


def get_job(job_id: str) -> dict[str, Any] | None:
    return db_get_job(job_id)


def _finish(job_id: str, *, result: dict[str, Any] | None = None, error: str | None = None) -> None:
    job = db_get_job(job_id)
    if not job:
        return
    job["status"] = "error" if error else "done"
    job["finished"] = datetime.now(UTC).isoformat()
    job["result"] = result
    job["error"] = error
    save_job(job)
    if result and result.get("output"):
        index_output(Path(result["output"]), fmt=result.get("format"), job_id=job_id)


async def run_convert_job(
    job_id: str,
    input_path: Path,
    output_format: str,
) -> None:
    loop = asyncio.get_running_loop()
    try:
        result = await loop.run_in_executor(None, convert_file, input_path, output_format)
        if result.get("success"):
            _finish(job_id, result=result)
        else:
            _finish(job_id, error=result.get("error", "convert failed"))
    except Exception as exc:
        _finish(job_id, error=str(exc))


def enqueue_convert(input_path: Path, output_format: str) -> dict[str, Any]:
    job_id = uuid.uuid4().hex[:8]
    job: dict[str, Any] = {
        "id": job_id,
        "name": f"convert → {output_format}",
        "status": "running",
        "input": str(input_path),
        "output_format": output_format,
        "started": datetime.now(UTC).isoformat(),
        "finished": None,
        "result": None,
        "error": None,
        "kind": "convert",
    }
    save_job(job)

    try:
        loop = asyncio.get_running_loop()
        task = loop.create_task(run_convert_job(job_id, input_path, output_format))
        _tasks.add(task)
        task.add_done_callback(_tasks.discard)
    except RuntimeError:
        result = convert_file(input_path, output_format)
        if result.get("success"):
            _finish(job_id, result=result)
        else:
            _finish(job_id, error=result.get("error", "convert failed"))
        job = db_get_job(job_id) or job

    return job
