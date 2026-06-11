# Features

libreoffice-mcp 0.2.x — general document automation, not PDF-only.

## Core operations

| Feature | MCP op | Description |
|---------|--------|-------------|
| Convert | `convert` | Single file → PDF, DOCX, ODT, XLSX, CSV, PPTX, HTML, … |
| Batch convert | `convert_batch` | Same format for many files |
| Document info | `document_info` | Writer / Calc / Impress detection + suggested formats |
| Template merge | `merge` | ODT `{{KEY}}` substitution → PDF/ODT |
| Markdown pack | `batch_pack` | Multiple `.md` → one PDF |
| PDF merge | `pdf_merge` | Combine PDFs (pypdf) |
| Folder watch | `watch_start` / `watch_stop` | Auto-convert on file change |
| Reveal output | `reveal_output` | Open file in OS file manager |
| Extension bridge | `bridge_discover`, `bridge_call` | Proxy to live LO MCP |

## Rich template merge

Placeholders `BODY`, `NARRATIVE`, `SUMMARY`, etc. accept **markdown** — converted to ODF paragraphs (headings, lists, bold/italic) before PDF export.

Bundled templates: `fleet-report.odt`, `fleet-board-pack.odt`, `fleet-artifact-pack.odt`. Add custom `.odt` files to `~/.libreoffice-mcp/templates/`.

## Webapp

| Page | Purpose |
|------|---------|
| Upload | Drag-drop → path for convert/workflows |
| Convert | Queue headless jobs |
| Workflows | Batch convert, PDF merge, folder watch, coworker merges |
| Tests | Self-test including live `soffice` |
| Chat | Agentic planner + execute |
| Output | Preview PDF/HTML, reveal in Explorer |

## Persistence

- Jobs stored in SQLite (`~/.libreoffice-mcp/data/libreoffice-mcp.db`)
- Output file index for recent exports

## Fleet / Fritz (optional)

Coworker flows still work via `fleet-agent-mcp` → `libreoffice(operation='merge', …)` on port 10981. See MCD `projects/libreoffice-mcp`.

## Live Writer (first-class)

| Feature | MCP op | Description |
|---------|--------|-------------|
| Live write | `live_write` | NL prompt → generate prose → typewriter in GUI |
| Live type | `live_type` | Type given text with pacing |
| Writer session | `writer_session_status`, `launch_writer` | Bridge health + open Writer |

See [LIVE_WRITER.md](LIVE_WRITER.md). **Not** arbitrary Basic macro files on disk — use `run_macro` / `run_python_macro` with the .oxt bridge, or extension `:8765` for third-party tools.

## Ecosystem

How we compare to **mcp-libre**, **libre-office-mcp**, and **WriterAgent** — and what to reuse: [COMPARISON-OTHER-LO-MCP.md](COMPARISON-OTHER-LO-MCP.md).

## Limits

- No embedded UNO in the MCP process — live lane uses Writer-side macro or extension bridge
- Complex Calc formulas / Impress animations not scripted — convert/export only
- Watch folder uses polling (default 5s), not OS inotify
