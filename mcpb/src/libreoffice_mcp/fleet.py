"""Fleet Apps Hub — read MCD webapp-registry.json."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from pydantic import BaseModel

from .config import settings

logger = logging.getLogger(__name__)


class FleetApp(BaseModel):
    id: str
    name: str
    port: int
    url: str
    repo: str | None = None
    repo_path: str | None = None
    description: str | None = None
    category: str | None = None
    tags: list[str] = []


def discover_fleet_from_docs() -> list[FleetApp]:
    mcd = Path(settings.central_docs_path)
    webapp_registry = mcd / "operations" / "webapp-registry.json"
    fleet_registry = mcd / "operations" / "fleet-registry.json"
    apps: dict[str, FleetApp] = {}

    if webapp_registry.is_file():
        try:
            data = json.loads(webapp_registry.read_text(encoding="utf-8"))
            for entry in data.get("webapps", []):
                app_id = entry.get("id")
                if not app_id:
                    continue
                tags = entry.get("tags", [])
                if "frontend" not in tags and "sota" not in tags:
                    continue
                port = int(entry.get("port") or 0)
                apps[app_id] = FleetApp(
                    id=app_id,
                    name=entry.get("label", app_id),
                    port=port,
                    url=f"http://localhost:{port}",
                    repo=entry.get("repo"),
                    repo_path=entry.get("repo_path"),
                    tags=tags,
                )
        except OSError as exc:
            logger.error("webapp-registry read failed: %s", exc)

    if fleet_registry.is_file():
        try:
            data = json.loads(fleet_registry.read_text(encoding="utf-8"))
            for entry in data.get("fleet", []):
                app_id = entry.get("id")
                if not app_id:
                    continue
                if app_id in apps:
                    apps[app_id].description = entry.get("description")
                    apps[app_id].category = entry.get("category")
                elif entry.get("port"):
                    port = int(entry["port"])
                    apps[app_id] = FleetApp(
                        id=app_id,
                        name=entry.get("name", app_id),
                        port=port,
                        url=f"http://localhost:{port}",
                        repo_path=entry.get("repo_path"),
                        category=entry.get("category"),
                    )
        except OSError as exc:
            logger.error("fleet-registry read failed: %s", exc)

    if not apps:
        logger.warning("No fleet apps from MCD — using fallback ports")
        for port in (10983, 10997, 10946, 10763, 10757):
            apps[f"app-{port}"] = FleetApp(
                id=f"app-{port}",
                name=f"App :{port}",
                port=port,
                url=f"http://localhost:{port}",
            )

    return sorted(apps.values(), key=lambda a: a.port)
