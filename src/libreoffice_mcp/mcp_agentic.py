"""MCP agentic workflow - ctx.sample() over LibreOffice operations (SEP-1577)."""

from __future__ import annotations

import json
import logging
from typing import Annotated, Any

from fastmcp import Context
from pydantic import Field

from .operations import execute_libreoffice_operation

logger = logging.getLogger(__name__)


async def libreoffice_agentic_workflow(
    goal: Annotated[
        str,
        Field(
            description="Natural-language document task (convert, merge, coworker PDF, batch pack)."
        ),
    ],
    ctx: Context,
) -> dict[str, Any]:
    """LIBREOFFICE_AGENTIC_WORKFLOW - Plan and execute multi-step LibreOffice tasks via sampling.

    Uses server-side Ollama (LIBREOFFICE_MCP_SAMPLING_*) or host sampling when configured.
    Wraps the libreoffice portmanteau operations as sampler tools.

    ## Return Format
    {"success": bool, "message": str, "recommendations": list[str]}

    ## Examples
    libreoffice_agentic_workflow(goal="Check soffice status and list fleet templates")
    libreoffice_agentic_workflow(goal="Convert C:/reports/weekly.md to PDF")
    """

    async def lo_status() -> str:
        r = await execute_libreoffice_operation("status")
        return json.dumps(r, ensure_ascii=False)[:8000]

    async def lo_list_templates() -> str:
        r = await execute_libreoffice_operation("list_templates")
        return json.dumps(r, ensure_ascii=False)[:8000]

    async def lo_convert(input_path: str, output_format: str = "pdf") -> str:
        r = await execute_libreoffice_operation(
            "convert",
            input_path=input_path,
            output_format=output_format,
            queue_job=False,
        )
        return json.dumps(r, ensure_ascii=False)[:8000]

    async def lo_merge(
        template: str,
        placeholders_json: str = "{}",
        output_format: str = "pdf",
        output_stem: str = "",
    ) -> str:
        try:
            placeholders = json.loads(placeholders_json) if placeholders_json.strip() else {}
            if not isinstance(placeholders, dict):
                placeholders = {}
        except json.JSONDecodeError:
            placeholders = {}
        r = await execute_libreoffice_operation(
            "merge",
            template=template,
            placeholders={str(k): str(v) for k, v in placeholders.items()},
            output_format=output_format,
            output_stem=output_stem or None,
        )
        return json.dumps(r, ensure_ascii=False)[:8000]

    async def lo_batch_pack(input_paths_csv: str, pack_title: str = "Document Pack") -> str:
        paths = [p.strip() for p in input_paths_csv.split(",") if p.strip()]
        r = await execute_libreoffice_operation(
            "batch_pack",
            input_paths=paths,
            pack_title=pack_title,
        )
        return json.dumps(r, ensure_ascii=False)[:8000]

    async def lo_bridge_discover() -> str:
        r = await execute_libreoffice_operation("bridge_discover")
        return json.dumps(r, ensure_ascii=False)[:8000]

    system_prompt = (
        "You are a LibreOffice document automation agent. Tools:\n"
        "- lo_status() - soffice path and extension bridge health\n"
        "- lo_list_templates() - bundled ODT templates (fleet-report, fleet-board-pack, fleet-artifact-pack)\n"
        "- lo_convert(input_path, output_format='pdf') - headless convert; .md renders to HTML first\n"
        "- lo_merge(template, placeholders_json='{\"TITLE\":\"...\"}', output_format='pdf', output_stem='')\n"
        "- lo_batch_pack(input_paths_csv='path1,path2', pack_title='...') - combine markdown files\n"
        "- lo_bridge_discover() - list extension MCP tools on :8765\n"
        "Coworker flows: weekly report → fleet-report.odt; board pack → fleet-board-pack.odt; "
        "artifact pack → fleet-artifact-pack.odt or batch markdown pack.\n"
        "Plan steps, call tools with absolute Windows paths when converting. Summarize outputs."
    )

    try:
        result = await ctx.sample(
            messages=goal,
            system_prompt=system_prompt,
            tools=[
                lo_status,
                lo_list_templates,
                lo_convert,
                lo_merge,
                lo_batch_pack,
                lo_bridge_discover,
            ],
            temperature=0.2,
            max_tokens=1024,
        )
        text = getattr(result, "text", None) or str(result)
        return {
            "success": True,
            "message": text or "No response from planner.",
            "recommendations": [
                "Ensure soffice is installed and LIBREOFFICE_MCP_SOFFICE_PATH is set if auto-detect fails.",
                "For local sampling, run Ollama and set LIBREOFFICE_MCP_SAMPLING_BASE_URL.",
            ],
        }
    except Exception as exc:
        logger.exception("Agentic workflow failed")
        return {
            "success": False,
            "error": str(exc),
            "error_type": "agentic_workflow",
            "recovery_options": [
                "Set LIBREOFFICE_MCP_SAMPLING_BASE_URL and run Ollama for server-side sampling.",
                "Set LIBREOFFICE_MCP_SAMPLING_USE_CLIENT_LLM=1 to use the host LLM.",
                "Call libreoffice(operation='status') directly to isolate headless issues.",
            ],
        }
