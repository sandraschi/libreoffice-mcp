# LibreOffice MCP — Server Identity & System Reference

## Identity

You are the **LibreOffice MCP** server — a FastMCP 3.3 document automation engine running
headless LibreOffice on the host. You convert, merge, batch-pack, watch-folders, and bridge
to live Writer/Calc extension MCP servers. You are the fleet's document factory.

**Version**: 0.3.0  
**Framework**: FastMCP 3.3  
**Transport**: dual — stdio (Claude Desktop / Cursor) and HTTP (Tauri webapp dashboard on port 10981)  
**Host requirement**: LibreOffice 26.x installed (`soffice.exe` or `soffice` binary)  
**Optional**: LibreOffice extension bridge (WriterAgent or mcp-libre `.oxt`) on port 8765 for live Writer/Calc editing, macro execution, and UNO automation  

## Architecture

LibreOffice MCP exposes 7 tools to the client:

| Tool | Type | Purpose |
|------|------|---------|
| `libreoffice` | Portmanteau | Core document operations (20+ ops in one tool) |
| `libreoffice_writer` | Portmanteau | Live Writer bridge — typewriter, macros, live_write |
| `libreoffice_calc` | Portmanteau | Live Calc bridge — cells, pivot tables, spreadsheet read |
| `libreoffice_agentic_workflow` | Sampling SEP-1577 | Multi-step document tasks via LLM planning |
| `libreoffice_help` | Discovery | Help index, topic lookup, format reference |
| `show_libreoffice_status_card` | Prefab App | In-chat rich UI card showing soffice + bridge health |
| `show_templates_card` | Prefab App | In-chat rich UI gallery of bundled ODT templates |

Additionally, the server registers three `@mcp.prompt()` templates (`libreoffice_quick_start`,
`libreoffice_coworker_pdf`, `libreoffice_convert_playbook`) and two Skills
(`libreoffice-expert/SKILL.md`, `coworker-pdf/SKILL.md`) via `SkillsDirectoryProvider`.

## Tool 1: `libreoffice` — Core Portmanteau

This is the primary tool. It accepts an `operation` parameter (Literal enum) that
selects the sub-operation. All other parameters are contextual — only the ones needed
for the selected operation are required.

### Operation: `status`

Check the full health of the LibreOffice MCP server. Returns:
- `soffice_found` — whether `soffice.exe` was detected
- `soffice_path` — resolved absolute path
- `extension_bridge` — online/offline status, tool count, URL
- `writer_bridge_connected` — real-time connection to the live Writer bridge
- `calc_bridge_connected` — connection state of the Calc bridge
- `templates_dir` and `output_dir` paths

Use this first, before any other operation, to confirm the server is configured correctly.
If `soffice_found` is false, set the `LIBREOFFICE_MCP_SOFFICE_PATH` env var or install
LibreOffice. If the extension bridge is offline, it just means live Writer/Calc features
are unavailable — headless convert and merge still work.

### Operation: `convert`

Convert a single document from one format to another. Parameters:
- `input_path` (required) — absolute path to the source file
- `output_format` (optional, default `"pdf"`) — target format
- `queue_job` (optional, default `false`) — if true, the conversion runs as a tracked
  background job visible in the webapp job queue

Supported conversions depend on the source document family:

| Input family | Extensions | Output formats |
|---|---|---|
| Writer | `.odt`, `.doc`, `.docx`, `.rtf`, `.txt`, `.md`, `.html`, `.htm`, `.pdf` | `pdf`, `docx`, `odt`, `html`, `txt`, `rtf` |
| Calc | `.ods`, `.xls`, `.xlsx`, `.csv`, `.tsv` | `pdf`, `xlsx`, `ods`, `csv`, `html` |
| Impress | `.odp`, `.ppt`, `.pptx` | `pdf`, `pptx`, `odp`, `html` |
| Draw | `.odg`, `.svg` | `pdf`, `svg` |

**Markdown to PDF flow**: When the input is a `.md` file, the server first renders the
markdown to HTML using a built-in renderer (with title extraction, heading hierarchy,
table support, and code block syntax highlighting) before passing to LibreOffice for
PDF export. This means you get styled, professional PDF output from plain markdown.

The output file is placed in `settings.output_dir` (default: `data/libreoffice-mcp/output/`)
and indexed in the output depot for retrieval via the webapp.

On failure, the response includes `suggested_formats` — a list of valid output formats
for the given input, derived from the detected document family.

### Operation: `convert_batch`

Convert multiple files in one call. Parameters:
- `input_paths` (required) — list of absolute file paths
- `output_format` (optional, default `"pdf"`)

Each file is converted independently. Failures on individual files do not stop the batch.
The response includes per-file results in a `results` array, plus summary counts.

### Operation: `document_info`

Inspect a document without converting it. Parameters:
- `input_path` (required)

Returns the detected document family (writer/calc/impress/draw/unknown), file extension,
size in bytes, family label, and suggested output formats. Useful before choosing an
output format for conversion.

### Operation: `merge`

Take a bundled ODT template and substitute `{{PLACEHOLDER}}` values, then optionally
convert to PDF or another format. Parameters:
- `template` (required) — name of the built-in template (e.g., `"fleet-report.odt"`)
  or an absolute path to a custom ODT file
- `placeholders` (required) — dictionary mapping placeholder keys to replacement values
- `output_format` (optional, default `"pdf"`)
- `output_stem` (optional) — base filename for the output (without extension)

Built-in templates (created automatically in the templates directory):

| Template | Placeholders | Use case |
|---|---|---|
| `fleet-report.odt` | `TITLE`, `DATE`, `SUMMARY`, `BODY` | Weekly/status report |
| `fleet-board-pack.odt` | `TITLE`, `DATE`, `KPI_TABLE`, `NARRATIVE`, `ACTION_ITEMS` | Board presentation pack |
| `fleet-artifact-pack.odt` | `TITLE`, `DATE`, `FILE_COUNT`, `BODY` | Combined artifact bundle |

The merge pipeline:
1. Open the ODT as a ZIP archive
2. Replace `{{KEY}}` occurrences in `content.xml` and `meta.xml` with provided values
3. Values are XML-escaped; newlines become `<text:line-break/>` elements
4. Save the merged ODT to `output_dir`
5. If `output_format` is not `"odt"`, run headless conversion to the target format

Placeholder values can be plain text or markdown. The `BODY` placeholder (and any
key that is detected as "rich" content) supports markdown-to-ODF-XML conversion,
preserving paragraphs, bold, italic, and lists.

### Operation: `list_templates`

List all available ODT templates. Returns an array of `{name, path, description, placeholders}`.

### Operation: `batch_pack`

Combine multiple markdown files into a single document and convert. Parameters:
- `input_paths` (required) — list of absolute `.md` file paths
- `pack_title` (optional) — title for the combined document (becomes the H1 heading)
- `output_stem` (optional) — base output filename
- `output_format` (optional, default `"pdf"`)

Pipeline:
1. Read each markdown file
2. Concatenate with `## {filename}` section headers and `---` separators
3. Write the combined markdown to `output_dir`
4. If format is `"md"`, return the markdown path directly
5. If format is `"html"`, render to HTML and return
6. Otherwise, convert the combined markdown through LibreOffice to the target format

### Operation: `pdf_merge`

Merge multiple existing PDF files into one. Parameters:
- `input_paths` (required) — list of absolute `.pdf` file paths
- `output_stem` (optional, default `"merged"`)

Uses `pypdf.PdfWriter` to concatenate PDFs. All inputs must be valid PDF files.

### Operation: `read_spreadsheet`

Read data from a spreadsheet file without launching a Calc GUI. Parameters:
- `input_path` (required) — path to `.ods`, `.xlsx`, `.xls`, or `.csv`

Returns sheet names, row counts, column headers, and sample data rows. Useful for
quick data extraction before conversion or processing.

### Operation: `reveal_output`

Open the output directory or a specific file in Windows Explorer. Parameters:
- `input_path` or `output_stem` — path to reveal

### Folder Watch Operations

Three operations for monitoring a directory and auto-converting new/changed files:

- `watch_start` — start watching a directory. Parameters: `watch_path` (required),
  `watch_glob` (optional, default `"*.*"`), `output_format` (optional, default `"pdf"`).
  The watcher runs in a background daemon thread, polling every N seconds (configurable).
  It tracks file mtimes to avoid duplicate conversions and skips `.tmp`, `.partial`, and
  `.db` files. Converted outputs are indexed in the depot.

- `watch_stop` — stop the active watch. Returns final status with processing count.

- `watch_status` — report the current watcher state without starting or stopping:
  running/not, watch path, glob pattern, output format, files processed, last error.

### Bridge Operations

Two operations for interacting with extension-hosted MCP servers (WriterAgent or
mcp-libre running on `http://127.0.0.1:8765/mcp`):

- `bridge_discover` — probe the extension bridge; returns online status, tool count,
  and a list of available tool names with descriptions (first 120 chars each).

- `bridge_call` — forward a tool call to the extension bridge. Parameters:
  `bridge_tool` (required) — name of the tool to call,
  `bridge_arguments` (optional) — dict of arguments to pass,
  `bridge_url` (optional) — override the default bridge URL.

### Live Writer Operations (delegated through `libreoffice`)

When the extension bridge is online, these operations interact with a running
LibreOffice Writer instance:

- `writer_session_status` — check if a Writer bridge session is connected
- `launch_writer` — open LibreOffice Writer (falls back to `start soffice --writer`
  if the bridge is offline)
- `live_write` — generate text via LLM and stream it into the open Writer document
  using the typewriter effect (configurable WPM).
  Parameters: `prompt` (what to write about), `max_words` (optional limit),
  `typewriter_wpm` (speed control), `prefer_session` (use bridge if available),
  `headless_fallback` (if bridge offline, write ODT and open Writer)
- `live_type` — inject a specific text string into the open Writer document.
  Parameters: `live_text` (the text to type), `typewriter_wpm`, same fallback options
- `list_macros` — list available UNO macros discovered via the extension bridge
- `run_macro` — execute a Basic UNO macro. Parameters: `macro_name`
  (e.g., `"Standard.Module1.MyMacro"`), `macro_language` (`"Basic"`), `macro_location`
  (`"application"` or `"document"`), `macro_library`, `macro_module`, `macro_args`
- `run_python_macro` — execute a Python UNO macro via the same parameters. Set
  `macro_language` to `"Python"`

### Operation: `help`

Returns the full operation catalog with supported formats per document family,
coworker flow descriptions, template names, and fleet port assignments.

## Tool 2: `libreoffice_writer` — Live Writer Bridge

A standalone portmanteau for live Writer operations. Overlaps with the Writer operations
in the main `libreoffice` tool but is dedicated to the Writer bridge workflow, keeping
the parameter surface focused on text and macros.

Operations: `status`, `live_write`, `live_type`, `insert_text`, `launch_writer`,
`run_macro`, `run_python_macro`, `list_macros`.

Additional parameters:
- `document_path` — open a specific existing document in Writer
- `text` — plain text for `insert_text` operation
- `macro_uri` — full `vnd.sun.star.script` URI for macro execution

The live Writer bridge requires the `libreoffice-mcp-bridge.oxt` extension installed
in LibreOffice. When the bridge is not reachable, operations fall back gracefully:
`live_write` and `live_type` can generate an ODT via headless conversion and open it
(if `headless_fallback=true`). Macro operations require the bridge to be online.

## Tool 3: `libreoffice_calc` — Live Calc Bridge

Live spreadsheet operations via the Calc extension bridge (`libreoffice-mcp-calc-bridge.oxt`).

Operations: `status`, `read_file`, `type_cells`, `live_pivot_demo`, `run_macro`,
`run_python_macro`, `list_macros`.

Key parameters:
- `input_path` — read an existing spreadsheet
- `sheet_name` — target sheet
- `row`, `col` — individual cell coordinates (0-based)
- `value` — cell value (string or number)
- `cells` — array of `{row, col, value}` objects for batch cell typing (typewriter effect)
- `delay_sec` — delay between cell entries for the typewriter demo
- `values` — 2D array for `set_range` bulk fill
- `source_range` — pivot source range (e.g., `"A1:D7"`)
- `dest_row`, `dest_col` — pivot table placement
- `row_field`, `data_field` — pivot dimension and measure
- `pivot_name` — pivot table object name
- `typewriter_seed` — auto-fill demo data before creating pivot

The `live_pivot_demo` operation is the showcase: it seeds a spreadsheet with demo data
(Region/Product/Revenue), then creates a Data Pilot pivot table, demonstrating end-to-end
Calc automation.

## Tool 4: `libreoffice_agentic_workflow` — Autonomous Document Tasks

This tool uses FastMCP sampling (`ctx.sample()`) with SEP-1577 tool-call iteration to
plan and execute multi-step LibreOffice operations autonomously. The LLM receives:

- A system prompt describing available tools (`lo_status`, `lo_list_templates`,
  `lo_convert`, `lo_merge`, `lo_batch_pack`, `lo_bridge_discover`)
- Your natural-language `goal`
- The ability to call these tools and use their results to decide next steps

Example goals:
- "Check soffice status and list fleet templates"
- "Convert C:/reports/weekly.md to PDF"
- "Create a board pack from fleet-board-pack.odt with Q3 KPIs"
- "Combine all .md files in C:/docs/ into a single PDF pack"

Sampling configuration:
- **Server-side**: Set `LIBREOFFICE_MCP_SAMPLING_BASE_URL` to an OpenAI-compatible endpoint
  (e.g., Ollama at `http://127.0.0.1:11434/v1`) and `LIBREOFFICE_MCP_SAMPLING_MODEL`
  (e.g., `qwen3.5:27b` or `gemma3:12b`).
- **Client-side**: Set `LIBREOFFICE_MCP_SAMPLING_USE_CLIENT_LLM=1` to use the host MCP
  client's own LLM (Claude Desktop, Cursor, etc.) instead of a separate Ollama instance.

If neither is configured, the tool returns an error with recovery options.

## Tool 5: `libreoffice_help` — Discovery

Parameter: `topic` (optional). If omitted, returns the full operation catalog.
Valid topics: `convert`, `merge`, `coworker`, `bridge`, `agentic`.

Returns code snippets, supported formats, template names, and fleet integration notes.

## Tool 6: `show_libreoffice_status_card` — Prefab Status

Renders an in-chat rich UI card showing:
- soffice detection status and path
- soffice version
- Extension bridge online/offline
- Bridge tool count
- Writer and Calc bridge session states

This is an `@mcp.tool(app=True)` Prefab App — in supporting MCP clients it renders as a
visual card; in others it falls back to a plain-text summary.

## Tool 7: `show_templates_card` — Prefab Template Gallery

Renders an in-chat rich UI card listing all bundled ODT templates with their descriptions
and placeholder keys. Clickable paths to each template file.

## Coworker PDF Flows (Fleet Integration)

LibreOffice MCP is the fleet's document factory. Three "coworker" flows produce PDF
deliverables consumed by `fleet-agent-mcp` for Fritz workflows:

1. **Weekly Report**: `libreoffice(operation="merge", template="fleet-report.odt",
   placeholders={TITLE, DATE, SUMMARY, BODY})` → PDF delivered to the output depot.

2. **Board Pack**: `libreoffice(operation="merge", template="fleet-board-pack.odt",
   placeholders={TITLE, DATE, KPI_TABLE, NARRATIVE, ACTION_ITEMS})` → PDF with KPIs,
   narrative section, and action item table.

3. **Artifact Pack**: Two paths:
   - Merge `fleet-artifact-pack.odt` with `TITLE, DATE, FILE_COUNT, BODY`
   - Or: `libreoffice(operation="batch_pack", input_paths=[...], pack_title="...")`
     to combine multiple markdown artifacts into one PDF.

## @mcp.prompt() Templates

Three prompt templates are registered:

- `libreoffice_quick_start` — setup checklist: install LibreOffice, set env vars,
  start HTTP mode, first convert
- `libreoffice_coworker_pdf` — coworker flow reference: which template for which
  deliverable, placeholder keys, agentic workflow alternative
- `libreoffice_convert_playbook` — conversion playbook: single file convert,
  batch convert, markdown-to-HTML-to-PDF pipeline, job queue tracking

## Skills

Two skills are exposed via `SkillsDirectoryProvider`:

- `libreoffice-expert/SKILL.md` — comprehensive reference for all LibreOffice
  operations, formato, formats, UNO macro patterns, and bridge configuration
- `coworker-pdf/SKILL.md` — step-by-step workflow for generating the three
  coworker PDF document types, including what placeholders to fill, how to
  format rich BODY content, and how to deliver to fleet-agent-mcp

## REST API & Webapp

In HTTP mode (port 10981), the server exposes:

- `GET /health` — full health check JSON
- `GET /api/v1/output` — list recent conversions
- `GET /api/v1/download/{filename}` — download a converted file
- `GET /api/v1/templates` — list templates
- `POST /api/v1/upload` — upload a file for conversion
- `POST /api/v1/convert` — REST endpoint for the convert operation
- `POST /api/v1/merge` — REST endpoint for template merge
- `GET /api/v1/jobs` — job queue status
- `POST /api/v1/watch/start` / `POST /api/v1/watch/stop` / `GET /api/v1/watch/status` — folder watch control
- `GET /docs` / `GET /openapi.json` / `GET /redoc` — FastAPI auto-generated API docs

The frontend (Vite/React dashboard on port 10983) proxies these endpoints and provides:
- **Dashboard** — live stats, health, connection status
- **Simple Actions** — convert, merge, batch pack forms
- **Workflows** — coworker PDF generators with placeholder forms
- **Templates** — gallery of bundled and custom ODT templates
- **Job Queue** — tracked background conversion jobs
- **Chat** — direct tool interaction
- **Tools** — dynamic tool discovery and schema browser
- **Skills** — skill content viewer
- **API Docs** — embedded Swagger UI + ReDoc

## Environment Variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `LIBREOFFICE_MCP_SOFFICE_PATH` | No | Auto-detected | Absolute path to soffice.exe |
| `LIBREOFFICE_MCP_EXTENSION_BRIDGE_URL` | No | `http://127.0.0.1:8765/mcp` | Extension MCP bridge URL |
| `LIBREOFFICE_MCP_SAMPLING_BASE_URL` | No | `http://127.0.0.1:11434/v1` | Ollama/OpenAI-compatible endpoint for agentic workflows |
| `LIBREOFFICE_MCP_SAMPLING_MODEL` | No | `qwen3.5:27b` | Model name for server-side sampling |
| `LIBREOFFICE_MCP_SAMPLING_USE_CLIENT_LLM` | No | `0` | Set to `1` to use host client LLM for sampling |
| `LIBREOFFICE_MCP_PREFAB_APPS` | No | `1` | Set to `0` to disable Prefab card registration |
| `LIBREOFFICE_MCP_PORT` | No | `10981` | HTTP server port |
| `LIBREOFFICE_MCP_HOST` | No | `127.0.0.1` | HTTP bind host |

## Output & Template Directories

- **Output**: `data/libreoffice-mcp/output/` — converted files are written here by default
- **Templates**: `data/libreoffice-mcp/templates/` — bundled ODT templates are created here
  on first startup. You can add custom `.odt` files to this directory and they will appear
  in `list_templates` results.

## Conversion Internals

The headless conversion engine:
1. Resolves the `soffice` binary path (configured or auto-detected)
2. For `.md` input: renders markdown to HTML via a built-in renderer with title extraction,
   heading levels (H1-H6), tables, fenced code blocks with syntax highlighting hints,
   and inline formatting (bold, italic, code)
3. Invokes `soffice --headless --norestore --invisible --convert-to {format} --outdir {dir} {path}`
4. Captures stdout/stderr for error reporting
5. Locates the output file by checking the expected filename, then falling back to
   recently-modified files in the output directory
6. Indexes successful conversions in the output depot

Timeout is configurable (default: 120 seconds). On timeout, the response includes the
input path and family so you can debug.

## Error Recovery

Common errors and their recovery paths:

- **"soffice not found"**: Set `LIBREOFFICE_MCP_SOFFICE_PATH` to the absolute path of
  your LibreOffice installation's `soffice.exe` (e.g., `C:\Program Files\LibreOffice\program\soffice.exe`)
- **"Extension bridge offline"**: The bridge is optional. Headless convert, merge,
  batch_pack, pdf_merge, and watch operations all work without it. Only live Writer/Calc
  and macro operations require the bridge.
- **"Conversion timed out"**: Large or complex documents may exceed the default 120s timeout.
  Retry with `queue_job=true` to run asynchronously, or split into smaller documents.
- **"Expected output missing"**: LibreOffice may produce a filename different from
  what was expected. Check the output directory manually or use `reveal_output`.
- **Sampling fails**: Ensure Ollama is running (`ollama serve`) or set
  `LIBREOFFICE_MCP_SAMPLING_USE_CLIENT_LLM=1`. For Ollama, pull a model first:
  `ollama pull qwen3.5:27b`.
- **pypdf not installed** (for pdf_merge): Run `uv sync` to install all dependencies.

## Fleet Integration

LibreOffice MCP integrates with:
- **fleet-agent-mcp**: Coworker PDF flows (weekly report, board pack, artifact pack)
  delivered to the output depot
- **qcad-mcp**: Convert DXF floor plans to PDF for sharing
- **freecad-mcp**: Convert CAD documentation from markdown to PDF
- **aiwatcher-mcp**: Generate digest PDFs from markdown summaries
- **email-mcp**: Attach converted PDFs to outgoing emails
- **arr-mcp**: Generate media library reports as PDF

The fleet exchange pattern: any fleet MCP can generate markdown content, then call
`libreoffice(operation="convert")` or `libreoffice(operation="batch_pack")` to
produce shareable PDF output.

## Document Format Matrix (Complete Reference)

### Input Detection

The server automatically detects the document family from the file extension:

| Extension | Family | Module |
|---|---|---|
| `.odt` | writer | LibreOffice Writer |
| `.doc` | writer | Legacy Word |
| `.docx` | writer | Word (OOXML) |
| `.rtf` | writer | Rich Text Format |
| `.txt` | writer | Plain text |
| `.md`, `.markdown` | writer | Markdown (rendered to HTML first) |
| `.html`, `.htm` | writer | HTML |
| `.pdf` | writer | PDF |
| `.ods` | calc | LibreOffice Calc |
| `.xls` | calc | Legacy Excel |
| `.xlsx` | calc | Excel (OOXML) |
| `.csv` | calc | Comma-separated values |
| `.tsv` | calc | Tab-separated values |
| `.odp` | impress | LibreOffice Impress |
| `.ppt` | impress | Legacy PowerPoint |
| `.pptx` | impress | PowerPoint (OOXML) |
| `.odg` | draw | LibreOffice Draw |
| `.svg` | draw | Scalable Vector Graphics |

### Output Format by Family

| Family | Available Output Formats |
|---|---|
| writer | `pdf`, `docx`, `odt`, `html`, `txt`, `rtf` |
| calc | `pdf`, `xlsx`, `ods`, `csv`, `html` |
| impress | `pdf`, `pptx`, `odp`, `html` |
| draw | `pdf`, `svg` |
| unknown | `pdf`, `html`, `odt`, `docx`, `xlsx`, `pptx` (broad fallback) |

The `unknown` family triggers a broad fallback — LibreOffice will attempt the conversion,
but results may vary depending on the actual file content. Always use `document_info` to
confirm the detected family before converting unrecognized formats.

## Markdown Rendering Pipeline

When converting `.md` files, the server applies this pipeline:

1. **Parse**: Read the markdown file as UTF-8
2. **Title extraction**: The first `# Heading` becomes the HTML `<title>` and document title
3. **HTML generation**: Markdown is converted to styled HTML with:
   - Heading levels H1-H6
   - Bold, italic, inline code, strikethrough
   - Ordered and unordered lists (nested)
   - Tables with header row styling
   - Fenced code blocks with language hints
   - Blockquotes
   - Horizontal rules
   - Links and images
4. **Save**: The HTML is written to a temporary file
5. **Convert**: `soffice --headless --convert-to {format} temp.html`
6. **Cleanup**: The temporary HTML is deleted

This pipeline produces professional-looking PDF output from plain markdown, suitable
for reports, documentation, and distribution.

## Extension Bridge Architecture

The optional extension bridge (`libreoffice-mcp-bridge.oxt`) runs inside LibreOffice
as a UNO extension. When installed and enabled, it:

- Starts an HTTP MCP server on port 8765 inside the LibreOffice process
- Exposes Writer tools: text insertion, content reading, formatting, macro execution
- Exposes Calc tools: cell manipulation, range operations, pivot table creation
- Exposes shared tools: macro discovery, document navigation, UNO API access
- Communicates via the FastMCP Streamable HTTP transport

The bridge is stateless — each tool call is independent. The LibreOffice document
state is persisted in the running LibreOffice instance.

To install: open LibreOffice → Tools → Extension Manager → Add → select
`dist/libreoffice-mcp-bridge.oxt`. Restart LibreOffice. The bridge starts
automatically and listens on port 8765.

## Resource Provider

The server registers one `@mcp.resource()`:

- `resource://libreoffice-mcp/capabilities` — machine-readable capability summary
  string listing all tools, skills, sampling configuration, and REST endpoints.

## Dual Transport Architecture

The server supports both transport modes in a single `server.py` entry point:

1. **stdio mode** (`--stdio`): Standard MCP over stdin/stdout. Used by Claude Desktop,
   Cursor, and other MCP clients that spawn the server as a subprocess.

2. **HTTP mode** (`--http --port 10981`): Full ASGI server via uvicorn. Mounts the
   MCP endpoint at `/mcp` (streamable HTTP transport), the FastAPI REST API at `/api`,
   and the webapp proxy routes. Used by the Tauri desktop wrapper and for direct
   HTTP access.

The `run_server.py` PyInstaller entry point detects `LIBREOFFICE_MCP_PORT` to switch
modes, enabling the embedded backend pattern for the Tauri NSIS installer.

## Sampling Architecture

The server's sampling handler (`LoSamplingHandler`) supports two modes:

- **Server-side** (default): Uses an OpenAI-compatible API endpoint
  (`LIBREOFFICE_MCP_SAMPLING_BASE_URL`) with a configurable model
  (`LIBREOFFICE_MCP_SAMPLING_MODEL`). Calls are made server-side via aiohttp.
  Supports any OpenAI-compatible endpoint including Ollama, LM Studio, vLLM,
  and cloud APIs.

- **Client-side** (`LIBREOFFICE_MCP_SAMPLING_USE_CLIENT_LLM=1`): Delegates to the
  host MCP client's LLM via FastMCP's `ctx.sample()`. This uses the same LLM that
  powers the agent (Claude, DeepSeek, etc.) and requires no separate Ollama instance.

The sampling handler behavior is set at server startup:
- `"always"`: Server-side sampling is always used (default)
- `"fallback"`: Server-side is tried first; falls back to client-side if unavailable

This is configured via `sampling_handler_behavior` in the `FastMCP(...)` constructor,
which reads `LIBREOFFICE_MCP_SAMPLING_USE_CLIENT_LLM`.
