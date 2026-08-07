"""Portmanteau dispatch for libreoffice_writer(operation=…)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, cast, get_args

from .live_session import writer_session_status as get_writer_session_status
from .live_write import live_type_text, live_write
from .macro_ops import (
    MacroLanguage,
    MacroLocation,
    build_macro_uri,
    list_macros_action,
    macro_action_payload,
)
from .writer_runtime import execute_writer_action, launch_writer_gui

WriterOp = Literal[
    "status",
    "help",
    "launch_writer",
    "live_write",
    "live_type",
    "insert_text",
    "new_document",
    "list_macros",
    "run_macro",
    "run_python_macro",
]


async def execute_libreoffice_writer_operation(
    operation: str,
    *,
    prompt: str | None = None,
    live_text: str | None = None,
    prefer_session: bool = True,
    headless_fallback: bool = True,
    typewriter_wpm: float | None = None,
    max_words: int | None = None,
    text: str | None = None,
    macro_uri: str | None = None,
    macro_name: str | None = None,
    macro_language: str = "Basic",
    macro_location: str = "application",
    macro_library: str | None = None,
    macro_module: str | None = None,
    macro_args: list[Any] | None = None,
    document_path: str | None = None,
) -> dict[str, Any]:
    from .config import settings

    if operation == "status":
        return {"success": True, "data": get_writer_session_status()}

    if operation == "help":
        return {
            "success": True,
            "message": "libreoffice_writer — live Writer typewriter + macros",
            "operations": list(get_args(WriterOp)),
            "install": "dist/libreoffice-mcp-bridge.oxt",
        }

    if operation == "launch_writer":
        return launch_writer_gui(
            document_path=Path(document_path) if document_path else None,
        )

    if operation == "live_write":
        if not prompt:
            return {"success": False, "error": "prompt required for live_write"}
        wpm = typewriter_wpm if typewriter_wpm is not None else settings.live_typewriter_wpm
        words = max_words if max_words is not None else settings.live_max_words
        result = await live_write(
            prompt,
            wpm=wpm,
            max_words=words,
            prefer_session=prefer_session,
            headless_fallback=headless_fallback,
        )
        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "next_steps": result.get("next_steps", []),
            "data": result,
        }

    if operation == "live_type":
        body = live_text or prompt or text
        if not body:
            return {"success": False, "error": "live_text, prompt, or text required"}
        wpm = typewriter_wpm if typewriter_wpm is not None else settings.live_typewriter_wpm
        result = await live_type_text(
            body,
            wpm=wpm,
            prefer_session=prefer_session,
            headless_fallback=headless_fallback,
        )
        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "next_steps": result.get("next_steps", []),
            "data": result,
        }

    if operation == "insert_text":
        if not (text or live_text):
            return {"success": False, "error": "text required for insert_text"}
        result = await execute_writer_action(
            {"action": "insert_text", "text": text or live_text},
            prefer_session=prefer_session,
            headless_fallback=headless_fallback,
        )
        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "next_steps": result.get("next_steps", []),
            "data": result,
        }

    if operation == "new_document":
        result = await execute_writer_action(
            {"action": "new_document"},
            prefer_session=prefer_session,
            headless_fallback=False,
        )
        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "next_steps": result.get("next_steps", []),
            "data": result,
        }

    if operation == "list_macros":
        result = await execute_writer_action(
            list_macros_action(),
            prefer_session=True,
            headless_fallback=False,
        )
        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "next_steps": result.get("next_steps", []),
            "data": result,
        }

    if operation in ("run_macro", "run_python_macro"):
        if not macro_uri and not macro_name:
            return {"success": False, "error": "macro_uri or macro_name required"}
        lang: MacroLanguage = (
            "Python"
            if operation == "run_python_macro"
            else cast(MacroLanguage, macro_language or "Basic")
        )
        loc = cast(MacroLocation, macro_location or "application")
        try:
            action = macro_action_payload(
                macro_uri=macro_uri,
                macro_name=macro_name,
                language=lang,
                location=loc,
                library=macro_library,
                module=macro_module,
                args=macro_args,
            )
        except ValueError as exc:
            return {"success": False, "error": str(exc)}
        result = await execute_writer_action(action, prefer_session=True, timeout=60.0)
        if macro_uri is None and macro_name:
            result["macro_uri"] = build_macro_uri(
                macro_name,
                language=lang,
                location=loc,
                library=macro_library,
                module=macro_module,
            )
        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "next_steps": result.get("next_steps", []),
            "data": result,
        }

    return {"success": False, "error": f"Unknown writer operation: {operation}"}
