"""Live typewriter writing — generate prose and insert into Writer session."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

import httpx

from .config import settings
from .live_session import emit_live_event, writer_session_connected
from .writer_runtime import execute_writer_action, headless_write_markdown, launch_writer_gui

log = logging.getLogger(__name__)


async def generate_prose(prompt: str, *, max_words: int = 400) -> str:
    """Generate short prose via Ollama (or return prompt echo when offline)."""
    system = (
        "You are a creative writer. Write vivid, readable prose only — no titles, "
        "no markdown headings, no meta commentary. Plain paragraphs."
    )
    full_prompt = f"{system}\n\nTopic: {prompt}\n\nWrite about {max_words} words or less."

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": full_prompt,
                    "stream": False,
                },
            )
            r.raise_for_status()
            body = r.json()
            text = (body.get("response") or "").strip()
            if text:
                return _clean_prose(text)
    except Exception as exc:
        log.warning("Ollama generate failed (%s); using template fallback", exc)

    return _clean_prose(
        f"{prompt.capitalize()} — a quiet morning, wings catching light between garden flowers. "
        "Each butterfly traced its own path, pausing on petals as if reading secrets written in nectar. "
        "The air shimmered with color: orange monarchs, pale cabbage whites, a single blue morpho "
        "that vanished and returned like a thought half-remembered. "
        "By noon the meadow felt like a living manuscript, every flutter a sentence the world was still writing."
    )


def _clean_prose(text: str) -> str:
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    return text.strip()


def _chunk_for_typewriter(text: str, *, chunk_chars: int = 12) -> list[str]:
    words = text.split()
    chunks: list[str] = []
    buf = ""
    for i, word in enumerate(words):
        piece = word + (" " if i < len(words) - 1 else "")
        if len(buf) + len(piece) <= chunk_chars:
            buf += piece
        else:
            if buf:
                chunks.append(buf)
            buf = piece
    if buf:
        chunks.append(buf)
    return chunks or [text]


async def live_type_text(
    text: str,
    *,
    wpm: float = 180.0,
    prefer_session: bool = True,
    headless_fallback: bool = True,
    new_document: bool = True,
) -> dict[str, Any]:
    """Type text into live Writer with visible pacing."""
    await emit_live_event({"type": "start", "chars": len(text), "mode": "live" if writer_session_connected() else "pending"})

    if new_document and prefer_session:
        await execute_writer_action(
            {"action": "new_document"},
            prefer_session=True,
            headless_fallback=False,
            timeout=25.0,
        )

    await emit_live_event({"type": "waiting_bridge", "message": "Start macro: Tools → Macros → Run → writer_bridge_macro → Main"})
    for _ in range(35):
        if writer_session_connected():
            break
        await asyncio.sleep(1)

    delay = max(0.02, 60.0 / max(wpm, 1.0) / 4.0)
    typed = ""
    chunks = _chunk_for_typewriter(text)

    for idx, chunk in enumerate(chunks):
        if prefer_session:
            result = await execute_writer_action(
                {"action": "insert_text", "text": chunk},
                prefer_session=True,
                headless_fallback=False,
                timeout=12.0,
            )
            if result.get("success") and result.get("session_used"):
                typed += chunk
                await emit_live_event(
                    {
                        "type": "chunk",
                        "text": chunk,
                        "typed_chars": len(typed),
                        "progress": round((idx + 1) / len(chunks), 3),
                    }
                )
                await asyncio.sleep(delay)
                continue
            break

    if len(typed) >= len(text.strip()) * 0.95:
        await emit_live_event({"type": "done", "typed_chars": len(typed), "mode": "live"})
        return {
            "success": True,
            "mode": "live",
            "session_used": True,
            "typed_chars": len(typed),
            "text_preview": text[:200],
        }

    if headless_fallback:
        await emit_live_event({"type": "fallback", "reason": "bridge_offline"})
        fb = await headless_write_markdown(text, output_stem="live-write")
        await emit_live_event({"type": "done", "mode": "headless_fallback", "output": fb.get("output")})
        return {**fb, "typed_chars": len(text), "text_preview": text[:200]}

    await emit_live_event({"type": "error", "message": "Writer bridge not connected"})
    return {
        "success": False,
        "error": "Writer bridge not connected. Open Writer and run docs/writer_bridge_macro.py (Main).",
        "mode": "unavailable",
        "session_used": False,
    }


async def live_write(
    prompt: str,
    *,
    wpm: float = 180.0,
    max_words: int = 400,
    prefer_session: bool = True,
    headless_fallback: bool = True,
    launch_writer: bool = True,
) -> dict[str, Any]:
    """Generate prose from prompt and type it live in Writer."""
    if launch_writer and not writer_session_connected():
        launch_writer_gui()

    await emit_live_event({"type": "generating", "prompt": prompt[:120]})
    text = await generate_prose(prompt, max_words=max_words)
    await emit_live_event({"type": "generated", "chars": len(text), "preview": text[:80]})

    result = await live_type_text(
        text,
        wpm=wpm,
        prefer_session=prefer_session,
        headless_fallback=headless_fallback,
        new_document=True,
    )
    return {
        **result,
        "prompt": prompt,
        "full_text": text,
    }
