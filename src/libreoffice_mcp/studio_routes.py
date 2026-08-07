"""REST routes for Live Studio hub."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .impress_outline import outline_to_odp
from .lo_gui import launch_lo_gui
from .studio import build_studio_session, resolve_output_path

studio_router = APIRouter(prefix="/studio", tags=["studio"])


class OpenInAppRequest(BaseModel):
    family: Literal["writer", "calc", "impress", "draw"] = Field(
        description="LibreOffice module to launch",
    )
    path: str | None = Field(
        default=None,
        description="Optional output filename (basename only, must live in output dir)",
    )


class OutlineToSlidesRequest(BaseModel):
    outline: str = Field(description="Markdown outline (# title, ## slides, - bullets)")
    title: str | None = Field(default=None, description="Optional deck title override")
    open_in_impress: bool = Field(default=False, description="Launch Impress GUI after build")


@studio_router.get("/session")
async def studio_session() -> dict:
    return {"success": True, "data": build_studio_session()}


@studio_router.post("/open-in-app")
async def studio_open_in_app(body: OpenInAppRequest) -> dict:
    document_path = None
    if body.path:
        try:
            document_path = resolve_output_path(body.path)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = launch_lo_gui(body.family, document_path)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Launch failed"))
    return {"success": True, **result}


@studio_router.post("/outline-to-slides")
async def studio_outline_to_slides(body: OutlineToSlidesRequest) -> dict:
    if not body.outline.strip():
        raise HTTPException(status_code=400, detail="outline required")
    result = outline_to_odp(
        body.outline,
        title=body.title,
        open_in_impress=body.open_in_impress,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Build failed"))
    return {"success": True, **result}
