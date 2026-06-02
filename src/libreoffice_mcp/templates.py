"""ODT template merge — placeholder substitution + optional convert."""

from __future__ import annotations

import re
import uuid
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from .config import settings
from .headless import convert_file
from .rich_odf import is_rich_placeholder, markdown_to_odf_xml
from .storage import index_output

_PLACEHOLDER = re.compile(r"\{\{([A-Z0-9_]+)\}\}")

# Minimal ODF namespaces for Writer documents
_CONTENT_NS = (
    'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
    'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
    'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
    'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" '
    'xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/" '
    'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"'
)

BUILTIN_TEMPLATE_VERSION = 2

_STYLES_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-styles office:version="1.2" {_CONTENT_NS}>
  <office:font-face-decls>
    <style:font-face style:name="Liberation Sans" svg:font-family="'Liberation Sans'"/>
    <style:font-face style:name="Liberation Serif" svg:font-family="'Liberation Serif'"/>
  </office:font-face-decls>
  <office:styles>
    <style:default-style style:family="paragraph">
      <style:text-properties style:font-name="Liberation Sans" fo:font-size="11pt" fo:color="#1e293b"/>
    </style:default-style>
    <style:style style:name="Standard" style:family="paragraph" style:class="text"/>
    <style:style style:name="DocTitle" style:family="paragraph">
      <style:text-properties fo:font-size="22pt" fo:font-weight="bold" fo:color="#1e3a5f"/>
      <style:paragraph-properties fo:margin-bottom="0.15cm"/>
    </style:style>
    <style:style style:name="DocMeta" style:family="paragraph">
      <style:text-properties fo:font-size="10pt" fo:color="#64748b" fo:font-style="italic"/>
      <style:paragraph-properties fo:margin-bottom="0.35cm"/>
    </style:style>
    <style:style style:name="SectionHeading" style:family="paragraph">
      <style:text-properties fo:font-size="14pt" fo:font-weight="bold" fo:color="#334155"/>
      <style:paragraph-properties fo:margin-top="0.45cm" fo:margin-bottom="0.12cm"/>
    </style:style>
    <style:style style:name="BodyText" style:family="paragraph">
      <style:text-properties fo:font-size="11pt" fo:color="#1e293b"/>
      <style:paragraph-properties fo:line-height="140%"/>
    </style:style>
    <style:style style:name="Bold" style:family="text">
      <style:text-properties fo:font-weight="bold"/>
    </style:style>
    <style:style style:name="Emphasis" style:family="text">
      <style:text-properties fo:font-style="italic"/>
    </style:style>
    <style:style style:name="List" style:family="paragraph">
      <style:paragraph-properties fo:margin-left="0.5cm"/>
    </style:style>
    <style:style style:name="Heading_20_1" style:family="paragraph">
      <style:text-properties fo:font-size="18pt" fo:font-weight="bold"/>
    </style:style>
  </office:styles>
  <office:automatic-styles>
    <style:page-layout style:name="FleetPage">
      <style:page-layout-properties fo:page-width="21.001cm" fo:page-height="29.7cm"
        fo:margin-top="2cm" fo:margin-bottom="2cm" fo:margin-left="2.2cm" fo:margin-right="2cm"/>
    </style:page-layout>
  </office:automatic-styles>
  <office:master-styles>
    <style:master-page style:name="Standard" style:page-layout-name="FleetPage"/>
  </office:master-styles>
</office:document-styles>
"""

_META_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-meta office:version="1.2" {_CONTENT_NS}>
  <office:meta>
    <meta:generator>libreoffice-mcp</meta:generator>
    <dc:title>{{{{TITLE}}}}</dc:title>
  </office:meta>
</office:document-meta>
"""

_MANIFEST_XML = """<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0">
  <manifest:file-entry manifest:media-type="application/vnd.oasis.opendocument.text" manifest:full-path="/"/>
  <manifest:file-entry manifest:media-type="text/xml" manifest:full-path="content.xml"/>
  <manifest:file-entry manifest:media-type="text/xml" manifest:full-path="styles.xml"/>
  <manifest:file-entry manifest:media-type="text/xml" manifest:full-path="meta.xml"/>
</manifest:manifest>
"""

BUILTIN_TEMPLATES: dict[str, dict[str, Any]] = {
    "fleet-report.odt": {
        "description": "Styled fleet report — TITLE, DATE, SUMMARY, BODY",
        "placeholders": ["TITLE", "DATE", "SUMMARY", "BODY"],
        "content": f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-content office:version="1.2" {_CONTENT_NS}>
  <office:body>
    <office:text>
      <text:h text:style-name="DocTitle" text:outline-level="1">{{{{TITLE}}}}</text:h>
      <text:p text:style-name="DocMeta">{{{{DATE}}}}</text:p>
      <text:p text:style-name="DocMeta">{{{{SUMMARY}}}}</text:p>
      <text:p text:style-name="BodyText"/>
      <text:h text:style-name="SectionHeading" text:outline-level="2">Details</text:h>
      <text:p text:style-name="BodyText">{{{{BODY}}}}</text:p>
    </office:text>
  </office:body>
</office:document-content>
""",
    },
    "fleet-board-pack.odt": {
        "description": "Board pack — TITLE, DATE, KPI_TABLE, NARRATIVE, ACTION_ITEMS",
        "placeholders": ["TITLE", "DATE", "KPI_TABLE", "NARRATIVE", "ACTION_ITEMS"],
        "content": f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-content office:version="1.2" {_CONTENT_NS}>
  <office:body>
    <office:text>
      <text:h text:style-name="DocTitle" text:outline-level="1">{{{{TITLE}}}}</text:h>
      <text:p text:style-name="DocMeta">{{{{DATE}}}}</text:p>
      <text:h text:style-name="SectionHeading" text:outline-level="2">KPI snapshot</text:h>
      <text:p text:style-name="BodyText">{{{{KPI_TABLE}}}}</text:p>
      <text:h text:style-name="SectionHeading" text:outline-level="2">Narrative</text:h>
      <text:p text:style-name="BodyText">{{{{NARRATIVE}}}}</text:p>
      <text:h text:style-name="SectionHeading" text:outline-level="2">Action items</text:h>
      <text:p text:style-name="BodyText">{{{{ACTION_ITEMS}}}}</text:p>
    </office:text>
  </office:body>
</office:document-content>
""",
    },
    "fleet-artifact-pack.odt": {
        "description": "Batch artifact pack — TITLE, DATE, FILE_COUNT, BODY",
        "placeholders": ["TITLE", "DATE", "FILE_COUNT", "BODY"],
        "content": f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-content office:version="1.2" {_CONTENT_NS}>
  <office:body>
    <office:text>
      <text:h text:style-name="DocTitle" text:outline-level="1">{{{{TITLE}}}}</text:h>
      <text:p text:style-name="DocMeta">{{{{DATE}}}} · {{{{FILE_COUNT}}}} files</text:p>
      <text:h text:style-name="SectionHeading" text:outline-level="2">Combined artifacts</text:h>
      <text:p text:style-name="BodyText">{{{{BODY}}}}</text:p>
    </office:text>
  </office:body>
</office:document-content>
""",
    },
}


def _write_odt(path: Path, content_xml: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "mimetype", "application/vnd.oasis.opendocument.text", compress_type=zipfile.ZIP_STORED
        )
        zf.writestr("META-INF/manifest.xml", _MANIFEST_XML)
        zf.writestr("content.xml", content_xml)
        zf.writestr("styles.xml", _STYLES_XML)
        zf.writestr("meta.xml", _META_XML)


def ensure_builtin_templates() -> list[str]:
    """Create or refresh bundled ODT templates under templates_dir."""
    settings.ensure_dirs()
    version_path = settings.templates_dir / ".builtin-version"
    try:
        installed = int(version_path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        installed = 0

    refresh = installed < BUILTIN_TEMPLATE_VERSION
    created: list[str] = []

    for name, spec in BUILTIN_TEMPLATES.items():
        target = settings.templates_dir / name
        if target.is_file() and not refresh:
            continue
        _write_odt(target, spec["content"])
        created.append(name)

    if refresh or created:
        version_path.write_text(str(BUILTIN_TEMPLATE_VERSION), encoding="utf-8")

    return created


def list_templates() -> list[dict[str, Any]]:
    ensure_builtin_templates()
    rows: list[dict[str, Any]] = []
    for path in sorted(settings.templates_dir.glob("*.odt")):
        spec = BUILTIN_TEMPLATES.get(path.name, {})
        rows.append(
            {
                "name": path.name,
                "path": str(path),
                "description": spec.get("description", "Custom ODT template"),
                "placeholders": spec.get("placeholders", []),
            }
        )
    return rows


def _escape_placeholder_value(value: str) -> str:
    """Escape for ODF XML text nodes; preserve newlines as separate paragraphs when needed."""
    return escape(value.replace("\r\n", "\n"))


def _apply_placeholders(text: str, placeholders: dict[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        raw = placeholders.get(key, "")
        if is_rich_placeholder(key, raw):
            return markdown_to_odf_xml(raw)
        if "\n" in raw:
            parts = [_escape_placeholder_value(line) for line in raw.split("\n") if line.strip()]
            return "<text:line-break/>".join(parts) if parts else ""
        return _escape_placeholder_value(raw)

    return _PLACEHOLDER.sub(repl, text)


def merge_odt_template(
    template_path: Path,
    placeholders: dict[str, str],
    *,
    output_stem: str | None = None,
) -> dict[str, Any]:
    """Substitute {{KEY}} placeholders in an ODT and write merged ODT to output_dir."""
    if not template_path.is_file():
        return {"success": False, "error": f"Template not found: {template_path}"}

    stem = output_stem or f"merged-{uuid.uuid4().hex[:8]}"
    merged_odt = settings.output_dir / f"{stem}.odt"
    settings.output_dir.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(template_path, "r") as zin:
            out_buf = BytesIO()
            with zipfile.ZipFile(out_buf, "w", zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    if item.filename == "mimetype":
                        zout.writestr(item, data, compress_type=zipfile.ZIP_STORED)
                        continue
                    if item.filename in {"content.xml", "meta.xml"}:
                        text = data.decode("utf-8")
                        text = _apply_placeholders(text, placeholders)
                        data = text.encode("utf-8")
                    zout.writestr(item, data)
            merged_odt.write_bytes(out_buf.getvalue())
    except (zipfile.BadZipFile, OSError, UnicodeDecodeError) as exc:
        return {"success": False, "error": f"Template merge failed: {exc}"}

    return {
        "success": True,
        "template": str(template_path),
        "output": str(merged_odt),
        "placeholders": list(placeholders.keys()),
    }


def merge_and_convert(
    template: str,
    placeholders: dict[str, str],
    output_format: str = "pdf",
    *,
    output_stem: str | None = None,
) -> dict[str, Any]:
    """Merge ODT template then headless convert to target format."""
    ensure_builtin_templates()
    template_path = Path(template)
    if not template_path.is_file():
        template_path = settings.templates_dir / template
    if not template_path.is_file():
        return {"success": False, "error": f"Template not found: {template}"}

    merged = merge_odt_template(template_path, placeholders, output_stem=output_stem)
    if not merged.get("success"):
        return merged

    if output_format.lower() in {"odt", ""}:
        merged["format"] = "odt"
        return merged

    converted = convert_file(Path(merged["output"]), output_format)
    if not converted.get("success"):
        return {**merged, "success": False, "error": converted.get("error"), "convert": converted}

    result = {
        "success": True,
        "template": str(template_path),
        "merged_odt": merged["output"],
        "output": converted.get("output"),
        "format": output_format,
        "placeholders": list(placeholders.keys()),
        "convert": converted,
    }
    if converted.get("output"):
        index_output(Path(converted["output"]), fmt=output_format)
    return result


def markdown_to_plain_body(md: str, *, max_chars: int = 6000) -> str:
    """Strip markdown noise for ODT BODY placeholders."""
    lines: list[str] = []
    for raw in md.splitlines():
        line = raw.strip()
        if not line:
            lines.append("")
            continue
        if line.startswith("#"):
            lines.append(line.lstrip("#").strip())
            continue
        line = re.sub(r"`([^`]+)`", r"\1", line)
        line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
        if line.startswith("- "):
            lines.append(f"• {line[2:]}")
        else:
            lines.append(line)
    text = "\n".join(lines).strip()
    if len(text) > max_chars:
        return text[: max_chars - 3] + "..."
    return text
