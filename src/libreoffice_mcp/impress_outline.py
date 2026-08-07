"""Build Impress decks from markdown-style outlines (Phase B)."""

from __future__ import annotations

import html
import re
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

from .config import settings
from .headless import find_soffice
from .lo_gui import launch_lo_gui


@dataclass
class Slide:
    title: str
    bullets: list[str]


def parse_markdown_outline(
    text: str, *, default_title: str = "Presentation"
) -> tuple[str, list[Slide]]:
    """Parse # title, ## slide headings, and - bullets into slides."""
    deck_title = default_title
    slides: list[Slide] = []
    current: Slide | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("# ") and not line.startswith("## "):
            deck_title = line[2:].strip() or deck_title
            continue
        if line.startswith("## "):
            if current:
                slides.append(current)
            current = Slide(title=line[3:].strip() or "Slide", bullets=[])
            continue
        if line.startswith("- "):
            if current is None:
                current = Slide(title="Slide", bullets=[])
            current.bullets.append(line[2:].strip())
            continue
        if current is None:
            current = Slide(title=line, bullets=[])
        else:
            current.bullets.append(line)

    if current:
        slides.append(current)

    if not slides:
        slides = [Slide(title=deck_title, bullets=["Add content"])]

    return deck_title, slides


def _bullet_xml(bullets: list[str]) -> str:
    if not bullets:
        return '<text:p text:style-name="TextBody"> </text:p>'
    parts = []
    for bullet in bullets:
        safe = html.escape(bullet)
        parts.append(f'<text:p text:style-name="TextBody">• {safe}</text:p>')
    return "".join(parts)


def _slide_xml(slide: Slide, index: int) -> str:
    title = html.escape(slide.title)
    return f"""
<draw:page draw:name="page{index}" draw:style-name="dp1" draw:master-page-name="Default">
  <draw:frame presentation:style-name="pr1" draw:layer="layout"
    svg:width="23cm" svg:height="3.2cm" svg:x="1.5cm" svg:y="1.2cm" presentation:class="title">
    <draw:text-box>
      <text:p text:style-name="Title">{title}</text:p>
    </draw:text-box>
  </draw:frame>
  <draw:frame presentation:style-name="pr2" draw:layer="layout"
    svg:width="23cm" svg:height="12cm" svg:x="1.5cm" svg:y="4.8cm" presentation:class="outline">
    <draw:text-box>
      {_bullet_xml(slide.bullets)}
    </draw:text-box>
  </draw:frame>
</draw:page>"""


def _build_content_xml(deck_title: str, slides: list[Slide]) -> str:
    pages = "".join(_slide_xml(slide, idx + 1) for idx, slide in enumerate(slides))
    html.escape(deck_title)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
  xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
  xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
  xmlns:presentation="urn:oasis:names:tc:opendocument:xmlns:presentation:1.0"
  xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"
  xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
  office:version="1.3">
  <office:automatic-styles>
    <style:style style:name="dp1" style:family="drawing-page"/>
    <style:style style:name="pr1" style:family="presentation" style:parent-style-name="Default-title"/>
    <style:style style:name="pr2" style:family="presentation" style:parent-style-name="Default-outline1"/>
    <style:style style:name="Title" style:family="paragraph"><style:text-properties fo:font-size="32pt" fo:font-weight="bold"/></style:style>
    <style:style style:name="TextBody" style:family="paragraph"><style:text-properties fo:font-size="18pt"/></style:style>
  </office:automatic-styles>
  <office:body>
    <office:presentation>
      <presentation:settings presentation:full-screen="false"/>
      <draw:page draw:name="dummy" draw:style-name="dp1" draw:master-page-name="Default" presentation:visibility="hidden"/>
      {pages}
    </office:presentation>
  </office:body>
</office:document-content>"""


def _manifest_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.3">
  <manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.presentation"/>
  <manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
  <manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>
  <manifest:file-entry manifest:full-path="meta.xml" manifest:media-type="text/xml"/>
</manifest:manifest>"""


def _styles_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<office:document-styles xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
  xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
  xmlns:presentation="urn:oasis:names:tc:opendocument:xmlns:presentation:1.0"
  office:version="1.3">
  <office:styles>
    <style:style style:name="Default" style:family="presentation"/>
    <style:style style:name="Default-title" style:family="presentation" style:parent-style-name="Default"/>
    <style:style style:name="Default-outline1" style:family="presentation" style:parent-style-name="Default"/>
    <draw:layer-set>
      <draw:layer draw:name="layout"/>
    </draw:layer-set>
  </office:styles>
  <office:master-styles>
    <style:master-page style:name="Default" style:page-layout-name="pm1" draw:style-name="dp1" presentation:visibility="visible"/>
  </office:master-styles>
</office:document-styles>"""


def _meta_xml(title: str) -> str:
    safe = html.escape(title)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-meta xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
  xmlns:dc="http://purl.org/dc/elements/1.1/" office:version="1.3">
  <office:meta>
    <meta:generator>libreoffice-mcp</meta:generator>
    <dc:title>{safe}</dc:title>
  </office:meta>
</office:document-meta>"""


def _safe_stem(title: str) -> str:
    stem = re.sub(r"[^\w\- ]+", "", title, flags=re.UNICODE).strip().replace(" ", "-")
    return stem[:60] or "outline-deck"


def write_odp(deck_title: str, slides: list[Slide], output_path: Path) -> None:
    """Write a minimal valid ODP zip to disk."""
    content = _build_content_xml(deck_title, slides)
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "mimetype",
            "application/vnd.oasis.opendocument.presentation",
            compress_type=zipfile.ZIP_STORED,
        )
        zf.writestr("META-INF/manifest.xml", _manifest_xml())
        zf.writestr("content.xml", content)
        zf.writestr("styles.xml", _styles_xml())
        zf.writestr("meta.xml", _meta_xml(deck_title))
    output_path.write_bytes(buffer.getvalue())


def outline_to_odp(
    outline: str,
    *,
    title: str | None = None,
    outdir: Path | None = None,
    open_in_impress: bool = False,
) -> dict[str, Any]:
    """Parse markdown outline and write `.odp` to the output directory."""
    if find_soffice() is None:
        return {
            "success": False,
            "error": "LibreOffice soffice not found. Set LIBREOFFICE_MCP_SOFFICE_PATH.",
        }

    deck_title, slides = parse_markdown_outline(outline, default_title=title or "Presentation")
    target_dir = outdir or settings.output_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{_safe_stem(deck_title)}.odp"
    output_path = target_dir / filename
    write_odp(deck_title, slides, output_path)

    launch_result = None
    if open_in_impress:
        launch_result = launch_lo_gui("impress", output_path)

    return {
        "success": True,
        "title": deck_title,
        "slide_count": len(slides),
        "output_path": str(output_path),
        "filename": filename,
        "launch": launch_result,
    }
