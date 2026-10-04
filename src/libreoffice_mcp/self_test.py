"""Backend self-tests for webapp Tests page and CI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import settings
from .formats import document_info
from .headless import find_soffice
from .templates import ensure_builtin_templates, list_templates, merge_odt_template


def run_self_tests(*, include_soffice: bool = True) -> dict[str, Any]:
    results: list[dict[str, Any]] = []

    def record(name: str, ok: bool, detail: str = "") -> None:
        results.append({"name": name, "ok": ok, "detail": detail})

    record("import_server", True)
    ensure_builtin_templates()
    templates = list_templates()
    record("builtin_templates", len(templates) >= 3, f"{len(templates)} templates")

    tpl = settings.templates_dir / "fleet-report.odt"
    if tpl.is_file():
        merged = merge_odt_template(
            tpl,
            {
                "TITLE": "Test",
                "DATE": "2026-01-01",
                "SUMMARY": "Hi",
                "BODY": "## Section\n\n**Bold** text",
            },
            output_stem="self-test-merge",
        )
        record(
            "template_merge_rich",
            merged.get("success", False),
            merged.get("error", merged.get("output", "")),
        )
    else:
        record("template_merge_rich", False, "fleet-report.odt missing")

    soffice = find_soffice()
    record("soffice_detected", soffice is not None, str(soffice) if soffice else "not found")

    if include_soffice and soffice is not None:
        from .headless import convert_file

        md = settings.output_dir / "self-test-sample.md"
        md.write_text("# Self Test\n\nConvert via soffice.\n", encoding="utf-8")
        conv = convert_file(md, "pdf")
        record(
            "soffice_convert_md_pdf",
            conv.get("success", False),
            conv.get("error") or conv.get("output", ""),
        )
        if conv.get("output"):
            info = document_info(Path(conv["output"]))
            record("document_info", bool(info.get("success", False)), str(info.get("family")))

    passed = sum(1 for r in results if r["ok"])
    return {
        "success": passed == len(results),
        "passed": passed,
        "total": len(results),
        "results": results,
    }
