"""Macro URI helpers and validation (execution runs in the .oxt bridge)."""

from __future__ import annotations

import re
from typing import Any, Literal

MacroLanguage = Literal["Basic", "Python"]
MacroLocation = Literal["application", "document"]

__all__ = ["MacroLanguage", "MacroLocation", "build_macro_uri", "macro_action_payload", "list_macros_action"]


def build_macro_uri(
    macro_name: str,
    *,
    language: MacroLanguage = "Basic",
    location: MacroLocation = "application",
    library: str | None = None,
    module: str | None = None,
) -> str:
    """Build a vnd.sun.star.script URI for the Writer bridge."""
    if macro_name.startswith("vnd.sun.star.script:"):
        return macro_name
    if library and module:
        path = f"{library}.{module}.{macro_name}"
    elif re.match(r"^[\w.]+\.[\w.]+$", macro_name):
        path = macro_name
    else:
        path = f"Standard.Module1.{macro_name}"
    return f"vnd.sun.star.script:{path}?language={language}&location={location}"


def macro_action_payload(
    *,
    macro_uri: str | None = None,
    macro_name: str | None = None,
    language: MacroLanguage = "Basic",
    location: MacroLocation = "application",
    library: str | None = None,
    module: str | None = None,
    args: list[Any] | tuple[Any, ...] | None = None,
) -> dict[str, Any]:
    """Structured action for the live Writer bridge queue."""
    action: dict[str, Any] = {
        "action": "run_python_macro" if language == "Python" else "run_macro",
        "language": language,
        "location": location,
    }
    if macro_uri:
        action["macro_uri"] = macro_uri
    elif macro_name:
        action["macro_name"] = macro_name
        if library:
            action["library"] = library
        if module:
            action["module"] = module
    else:
        raise ValueError("macro_uri or macro_name required")
    if args is not None:
        action["args"] = list(args)
    return action


def list_macros_action() -> dict[str, Any]:
    return {"action": "list_macros"}
