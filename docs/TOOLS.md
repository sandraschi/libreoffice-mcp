# MCP tool reference

Portmanteau: **`libreoffice(operation=…)`**

## Operations

| Operation | Description |
|-----------|-------------|
| `status` | `soffice` path, version, extension bridge |
| `document_info` | Writer/Calc/Impress family + suggested formats |
| `convert` | Headless single-file convert |
| `convert_batch` | Many files, one output format |
| `merge` | ODT template merge → pdf/odt/docx |
| `list_templates` | Bundled + custom templates |
| `batch_pack` | Multiple markdown → one PDF |
| `pdf_merge` | Combine PDF files |
| `watch_start` | Auto-convert folder (`watch_path`, `watch_glob`) |
| `watch_stop` | Stop folder watch |
| `watch_status` | Watch state |
| `reveal_output` | Open output in file manager |
| `bridge_discover` | Extension MCP tools on :8765 |
| `bridge_call` | Proxy tool to extension |
| `help` | Capability summary |

## Format hints

| Family | Extensions | Common exports |
|--------|------------|----------------|
| Writer | odt, docx, md, html, rtf | pdf, docx, odt, html |
| Calc | ods, xlsx, csv | pdf, xlsx, csv, ods |
| Impress | odp, pptx | pdf, pptx, odp |

## Examples

```python
# Convert spreadsheet
libreoffice(operation="convert", input_path="/data/sheet.ods", output_format="xlsx")

# Presentation to PDF
libreoffice(operation="convert", input_path="/slides/deck.odp", output_format="pdf")

# Merge template with markdown body
libreoffice(
    operation="merge",
    template="fleet-report.odt",
    placeholders={"TITLE": "Q1", "DATE": "2026-05-30", "SUMMARY": "Done", "BODY": "## Highlights\n\n- Item one"},
    output_format="pdf",
)

# PDF merge
libreoffice(operation="pdf_merge", input_paths=["a.pdf", "b.pdf"], output_stem="combined")

# Watch incoming scans
libreoffice(operation="watch_start", watch_path="C:/Scans/Inbox", watch_glob="*.pdf", output_format="pdf")
```

## Other MCP tools

- `libreoffice_help(topic=…)`
- `libreoffice_agentic_workflow(goal=…)`
- `show_libreoffice_status_card`, `show_templates_card` (prefabs)

## REST mirror

All operations available via `/api/*` — see OpenAPI at `/docs` when backend is running.

Key routes: `POST /api/upload`, `POST /api/convert/batch`, `POST /api/pdf/merge`, `GET /api/tests/run`, `POST /api/chat`.
