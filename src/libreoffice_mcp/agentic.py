"""Rule-based agentic planner for LibreOffice MCP webapp goals."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

from .config import settings
from .workflows import COMPLEX_WORKFLOWS, SIMPLE_ACTIONS, run_simple_action, run_workflow

_INTENT_RULES: list[tuple[re.Pattern[str], dict[str, Any]]] = [
    (
        re.compile(r"\b(write|story|typewriter|live write|short story|watch.*writ)\b", re.I),
        {
            "kind": "action",
            "action_id": "live_write",
            "reason": "Live Writer typewriter — watch it write in GUI",
        },
    ),
    (
        re.compile(r"\b(status|health|soffice|bridge)\b", re.I),
        {"kind": "action", "action_id": "status", "reason": "Goal mentions system health"},
    ),
    (
        re.compile(r"\b(bridge|extension|writeragent|8765)\b", re.I),
        {
            "kind": "action",
            "action_id": "bridge_discover",
            "reason": "Goal mentions extension bridge",
        },
    ),
    (
        re.compile(r"\b(template|list template)\b", re.I),
        {"kind": "action", "action_id": "list_templates", "reason": "Goal asks for templates"},
    ),
    (
        re.compile(r"\b(board pack|board_pack|coworker_board)\b", re.I),
        {
            "kind": "workflow",
            "workflow_id": "coworker_board_pack",
            "reason": "Board pack coworker flow",
        },
    ),
    (
        re.compile(r"\b(weekly report|fleet report|coworker_weekly)\b", re.I),
        {
            "kind": "workflow",
            "workflow_id": "coworker_weekly_report_pdf",
            "reason": "Weekly report coworker flow",
        },
    ),
    (
        re.compile(r"\b(artifact pack|coworker_artifact)\b", re.I),
        {
            "kind": "workflow",
            "workflow_id": "coworker_artifact_pack",
            "reason": "Artifact pack merge flow (fleet-artifact-pack.odt)",
        },
    ),
    (
        re.compile(r"\b(batch pack|markdown pack|combine markdown)\b", re.I),
        {
            "kind": "workflow",
            "workflow_id": "batch_markdown_pack",
            "reason": "Batch markdown pack",
        },
    ),
    (
        re.compile(r"\b(merge pdf|pdf merge|combine pdf)\b", re.I),
        {
            "kind": "workflow",
            "workflow_id": "pdf_merge",
            "reason": "Merge multiple PDFs",
        },
    ),
    (
        re.compile(r"\b(watch folder|auto convert|folder watch)\b", re.I),
        {
            "kind": "workflow",
            "workflow_id": "folder_watch",
            "reason": "Watch folder and auto-convert",
        },
    ),
    (
        re.compile(r"\b(spreadsheet|xlsx|csv|calc)\b", re.I),
        {
            "kind": "action",
            "action_id": "convert",
            "reason": "Spreadsheet conversion",
            "default_format": "xlsx",
        },
    ),
    (
        re.compile(r"\b(presentation|pptx|slides|impress)\b", re.I),
        {
            "kind": "action",
            "action_id": "convert",
            "reason": "Presentation conversion",
            "default_format": "pdf",
        },
    ),
    (
        re.compile(r"\b(convert|pdf|docx|odt)\b", re.I),
        {"kind": "action", "action_id": "convert", "reason": "Goal mentions conversion"},
    ),
    (
        re.compile(r"\b(merge|placeholder|odt)\b", re.I),
        {"kind": "action", "action_id": "quick_merge", "reason": "Goal mentions template merge"},
    ),
]


def _extract_path(goal: str) -> str | None:
    win = re.search(r"[A-Za-z]:[/\\][^\s\"']+", goal)
    if win:
        return win.group(0)
    posix = re.search(r"(?:/[\w.-]+)+", goal)
    return posix.group(0) if posix else None


def plan_goal(goal: str) -> dict[str, Any]:
    """Return a structured plan without executing."""
    goal = goal.strip()
    if not goal:
        return {"success": False, "error": "goal required"}

    steps: list[dict[str, Any]] = []
    matched: dict[str, Any] | None = None

    for pattern, spec in _INTENT_RULES:
        if pattern.search(goal):
            matched = spec
            break

    if matched:
        if matched["kind"] == "action":
            action = next((a for a in SIMPLE_ACTIONS if a["id"] == matched["action_id"]), None)
            params: dict[str, Any] = {}
            if matched["action_id"] == "live_write":
                params["prompt"] = goal
            if matched["action_id"] == "convert":
                path = _extract_path(goal)
                if path:
                    params["input_path"] = path
                fmt = matched.get("default_format")
                if not fmt:
                    if re.search(r"\bxlsx\b", goal, re.I):
                        fmt = "xlsx"
                    elif re.search(r"\bcsv\b", goal, re.I):
                        fmt = "csv"
                    elif re.search(r"\bpptx\b", goal, re.I):
                        fmt = "pptx"
                    elif re.search(r"\bdocx\b", goal, re.I):
                        fmt = "docx"
                    elif re.search(r"\bodt\b", goal, re.I):
                        fmt = "odt"
                    elif re.search(r"\bhtml\b", goal, re.I):
                        fmt = "html"
                    else:
                        fmt = "pdf"
                params["output_format"] = fmt
            steps.append(
                {
                    "type": "simple_action",
                    "action_id": matched["action_id"],
                    "label": action["label"] if action else matched["action_id"],
                    "params": params,
                    "reason": matched["reason"],
                }
            )
        else:
            wf = next((w for w in COMPLEX_WORKFLOWS if w["id"] == matched["workflow_id"]), None)
            steps.append(
                {
                    "type": "workflow",
                    "workflow_id": matched["workflow_id"],
                    "label": wf["label"] if wf else matched["workflow_id"],
                    "params_hint": "Fill placeholders on the Workflows page or pass placeholders in execute payload",
                    "reason": matched["reason"],
                }
            )
    else:
        steps.append(
            {
                "type": "guidance",
                "message": (
                    "Describe: convert paths (Writer/Calc/Impress), template merge, PDF merge, "
                    "batch markdown pack, folder watch, or extension bridge. "
                    "Upload files on the Upload page when paths are not available."
                ),
            }
        )

    return {
        "success": True,
        "goal": goal,
        "steps": steps,
        "available_operations": [a["id"] for a in SIMPLE_ACTIONS]
        + [w["id"] for w in COMPLEX_WORKFLOWS],
        "message": steps[0].get("reason") or steps[0].get("message", "Plan ready"),
    }


async def execute_plan(
    goal: str,
    *,
    params: dict[str, Any] | None = None,
    execute: bool = False,
) -> dict[str, Any]:
    plan = plan_goal(goal)
    if not plan.get("success"):
        return plan

    if not execute:
        return plan

    params = params or {}
    results: list[dict[str, Any]] = []
    for step in plan.get("steps", []):
        if step.get("type") == "simple_action":
            merged = {**step.get("params", {}), **params}
            result = await run_simple_action(step["action_id"], merged)
            results.append(result)
            if not result.get("success"):
                return {
                    **plan,
                    "executed": True,
                    "success": False,
                    "results": results,
                    "error": result.get("error", "Action failed"),
                }
        elif step.get("type") == "workflow":
            result = await run_workflow(step["workflow_id"], params)
            results.append(result)
            if not result.get("success"):
                return {
                    **plan,
                    "executed": True,
                    "success": False,
                    "results": results,
                    "error": result.get("error", "Workflow failed"),
                }

    if not results:
        return {**plan, "executed": False, "message": plan.get("message")}

    return {
        **plan,
        "executed": True,
        "success": all(r.get("success") for r in results),
        "results": results,
        "message": "Agentic execution completed",
    }


async def llm_enrich_plan(goal: str, plan: dict[str, Any]) -> dict[str, Any]:
    """Optional Ollama pass to suggest params — best-effort, never required."""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/chat",
                json={
                    "model": settings.ollama_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You assist LibreOffice MCP. Reply with JSON only: "
                                '{"hint":"one sentence","suggested_params":{}}'
                            ),
                        },
                        {
                            "role": "user",
                            "content": f"Goal: {goal}\nPlan: {json.dumps(plan.get('steps', []))}",
                        },
                    ],
                    "stream": False,
                },
            )
            if not r.is_success:
                return plan
            content = r.json().get("message", {}).get("content", "")
            match = re.search(r"\{.*\}", content, re.S)
            if match:
                plan["llm_hint"] = json.loads(match.group(0))
    except (httpx.HTTPError, json.JSONDecodeError, KeyError):
        pass
    return plan
