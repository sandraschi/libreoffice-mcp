---
name: libreoffice-expert
description: Headless LibreOffice convert, ODT merge, batch pack, live Writer/Calc bridges, and extension proxy operations.
---

# LibreOffice MCP — Operations

Headless Writer/Calc/Impress automation plus optional live GUI bridges.
Backend `:10981` (REST + MCP `/mcp`), dashboard `:10983`, extension bridge `:8765`.

## Who should use what

| Caller | Path | When |
|--------|------|------|
| **Agent (you)** | MCP tools below (`libreoffice(operation=…)`, …) | Any automated document task — prefer tools over the webapp |
| **Human** | Dashboard pages: Convert, Templates, Pack, Output, Jobs, LiveWrite, LiveCalc, Upload | Interactive/one-off work, visual preview, drag-drop upload |
| **Either** | REST `/api/*` (mirrors every operation) | Scripts, CI, or when MCP transport is unavailable |

Start every session with `libreoffice(operation="status")` — it reports `soffice`
path/version, bridge health, and output dirs. If `soffice_found` is false, fix
the install first (see Troubleshooting); nothing else will work.

## Prerequisites

- LibreOffice 26.x with `soffice` on PATH, or set `LIBREOFFICE_MCP_SOFFICE_PATH`
  (Windows default `C:\Program Files\LibreOffice\program\soffice.exe`).
- Optional live editing: install `dist/libreoffice-mcp-bridge.oxt` (Writer) and/or
  `dist/libreoffice-mcp-calc-bridge.oxt` (Calc), or run WriterAgent/mcp-libre on
  `http://127.0.0.1:8765/mcp` for `bridge_*` ops.
- Optional agentic enrichment: Ollama at `LIBREOFFICE_MCP_SAMPLING_BASE_URL`
  (default `http://127.0.0.1:11434/v1`). Without any LLM, Chat and
  `libreoffice_agentic_workflow` fall back to the rule-based planner.

## Tool catalog

### `libreoffice(operation=…)` — main portmanteau

| Operation | Purpose | Key params |
|-----------|---------|------------|
| `status` | soffice path/version + bridge health | — |
| `help` | Capability summary + REST routes | — |
| `convert` | Headless single-file convert (`.md` renders to HTML first) | `input_path`, `output_format`, `queue_job` |
| `convert_batch` | Many files, one output format | `input_paths`, `output_format` |
| `document_info` | Writer/Calc/Impress family + suggested exports | `input_path` |
| `merge` | ODT template `{{PLACEHOLDER}}` → pdf/odt/docx | `template`, `placeholders`, `output_format`, `output_stem` |
| `list_templates` | Bundled + custom ODT templates | — |
| `batch_pack` | Multiple `.md` → single styled PDF | `input_paths`, `pack_title` |
| `pdf_merge` | Combine PDFs (pypdf) | `input_paths`, `output_stem` |
| `watch_start` / `watch_stop` / `watch_status` | Auto-convert folder | `watch_path`, `watch_glob`, `output_format` |
| `read_spreadsheet` | Headless spreadsheet read | `input_path` |
| `reveal_output` | Open output in OS file manager | `input_path` |
| `writer_session_status` / `launch_writer` | Live Writer bridge state / open GUI | — |
| `live_write` | Prompt → agentic draft, typed live in Writer | `prompt`, `prefer_session`, `headless_fallback`, `max_words`, `typewriter_wpm` |
| `live_type` | Type given text live with pacing | `live_text`, `typewriter_wpm` |
| `run_macro` / `run_python_macro` / `list_macros` | UNO macros via `.oxt` bridge | `macro_uri` or `macro_name` + `macro_language`, `macro_location`, `macro_args` |
| `bridge_discover` / `bridge_call` | List / proxy extension MCP tools on `:8765` | `bridge_tool`, `bridge_arguments`, `bridge_url` |

`output_format` values: `pdf`, `docx`, `odt`, `html`, `xlsx`, `csv` (family-dependent —
check `document_info` first when unsure).

### `libreoffice_writer(operation=…)` — live Writer

`status`, `help`, `launch_writer`, `live_write`, `live_type`, `insert_text`
(`text`), `new_document`, `list_macros`, `run_macro`, `run_python_macro`.
Extra param: `document_path` (open an existing document first).

### `libreoffice_calc(operation=…)` — live Calc

`status`, `help`, `launch_calc`, `read_file` (`input_path`, `sheet_name`, `max_rows`),
`live_type_grid`, `live_pivot_demo`, `set_cell` (`row`, `col`, `value`),
`set_range` (`start_row/col`, `end_row/col`, `values`), `type_cells` (`cells`,
`delay_sec`), `get_range`, `sheet_info`, `seed_demo`, `create_pivot`
(`source_range`, `dest_row/col`, `row_field`, `data_field`, `pivot_name`),
plus `run_macro` / `run_python_macro`.

### Companion tools

- `libreoffice_help(topic=…)` — topics: `convert`, `merge`, `coworker`, `bridge`, `agentic`.
- `libreoffice_agentic_workflow(goal=…)` — multi-step plans via sampling (SEP-1577);
  simple actions: `status`, `live_write`, `writer_session_status`, `bridge_discover`,
  `list_templates`, `convert`, `document_info`, `pdf_merge`, `quick_merge`;
  workflows: `coworker_weekly_report_pdf`, `coworker_board_pack`,
  `coworker_artifact_pack`, `batch_markdown_pack`, `pdf_merge`, `folder_watch`,
  `convert_batch`, `bridge_call`.
- `show_libreoffice_status_card`, `show_templates_card` — in-chat Prefab UI.

## Workflows (copy-paste shapes)

```python
# 1. Single convert, tracked as a job for the webapp Jobs page
libreoffice(operation="convert", input_path="C:/docs/report.md",
            output_format="pdf", queue_job=True)

# 2. ODT template merge (rich markdown allowed in BODY fields)
libreoffice(operation="merge", template="fleet-report.odt", output_format="pdf",
            placeholders={"TITLE": "Weekly", "DATE": "2026-10-04",
                          "SUMMARY": "Shipped.", "BODY": "## Highlights\n\n- Item one"})

# 3. Batch pack: many markdown files -> one PDF
libreoffice(operation="batch_pack", input_paths=["a.md", "b.md"],
            pack_title="Sprint Pack")

# 4. Combine PDFs
libreoffice(operation="pdf_merge", input_paths=["a.pdf", "b.pdf"],
            output_stem="combined")

# 5. Watch a scans folder (PDF in, converted out)
libreoffice(operation="watch_start", watch_path="C:/Scans/Inbox",
            watch_glob="*.pdf", output_format="pdf")

# 6. Live write: prompt -> watch Writer type (falls back to headless ODT)
libreoffice_writer(operation="live_write", prompt="Draft a Q3 memo",
                   max_words=300)

# 7. Calc pivot demo: seed typewriter data + Data Pilot pivot
libreoffice_calc(operation="live_pivot_demo", source_range="A1:D7",
                 row_field="Region", data_field="Revenue")

# 8. Proxy a live extension tool
libreoffice(operation="bridge_call", bridge_tool="<name-from-bridge_discover>",
            bridge_arguments={})
```

Template placeholder sets: `fleet-report.odt` → TITLE, DATE, SUMMARY, BODY;
`fleet-board-pack.odt` → TITLE, DATE, KPI_TABLE, NARRATIVE, ACTION_ITEMS;
`fleet-artifact-pack.odt` → TITLE, DATE, FILE_COUNT, BODY.
Outputs land in `~/.libreoffice-mcp/output/` (or `LIBREOFFICE_MCP_OUTPUT_DIR`);
list them via Jobs/Output pages or `GET /api/output`.

## REST mirror

Every operation has an `/api/*` route (`POST /api/convert`, `/api/merge`,
`/api/pack`, `/api/pdf/merge`, `/api/watch/start`, …) plus `GET /health`,
`GET /api/v1/diagnostics` (smoke-test probe), `POST /api/shutdown` (orderly exit),
`GET /api/llm/providers|models|onboarding`, `POST /api/llm/chat`. Full schema at
`/docs` (Swagger) when the backend runs.

## Troubleshooting

| Symptom | Cause → fix |
|---------|-------------|
| `soffice not found` / `soffice_available: false` | Install LibreOffice 26.x; set `LIBREOFFICE_MCP_SOFFICE_PATH` in `.env` or Settings page |
| Convert job error, no output | Missing input path or unsupported format (`document_info` first); `soffice` timeout → raise `LIBREOFFICE_MCP_CONVERT_TIMEOUT_SEC`; job stderr is in the Jobs page/detail |
| Merge produces empty fields | Placeholder keys must match exactly (`{{TITLE}}` ≠ `{{Title}}`); list expected keys via `list_templates` + template docs |
| `live_write` opens Writer instead of typing | Live bridge offline — expected headless fallback. Start the `.oxt` bridge macro for live typing |
| `bridge_discover` empty/offline | Normal without WriterAgent/mcp-libre on `:8765`. Headless ops unaffected |
| Watch converts nothing | `watch_status` must show the folder active; only supported extensions convert; tune `LIBREOFFICE_MCP_WATCH_POLL_SEC` |
| PDF merge fails | Encrypted/corrupt inputs — pypdf error surfaces in the job result |
| Upload rejected | Over `LIBREOFFICE_MCP_MAX_UPLOAD_BYTES` (default 50 MB) or disk full under `~/.libreoffice-mcp/uploads` |
| Chat never uses LLM | No provider online — set sampling base URL / start Ollama; rule-based planner still works |
| Dashboard can't reach backend | Ports `10981`/`10983` busy — `just webapp` clears zombies; check `GET /health` directly |

## Configuration (core env)

`LIBREOFFICE_MCP_SOFFICE_PATH`, `LIBREOFFICE_MCP_EXTENSION_BRIDGE_URL`
(default `http://127.0.0.1:8765/mcp`), `LIBREOFFICE_MCP_TEMPLATES_DIR`,
`LIBREOFFICE_MCP_OUTPUT_DIR`, `LIBREOFFICE_MCP_CONVERT_TIMEOUT_SEC` (120),
`LIBREOFFICE_MCP_WATCH_POLL_SEC` (5), `LIBREOFFICE_MCP_MAX_UPLOAD_BYTES`,
`LIBREOFFICE_MCP_SAMPLING_BASE_URL` + `LIBREOFFICE_MCP_SAMPLING_MODEL`,
`LIBREOFFICE_MCP_CENTRAL_DOCS_PATH` (Apps Hub registry). Template: `.env.example`.
