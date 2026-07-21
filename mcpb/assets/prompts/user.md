# LibreOffice MCP — User Guide & Tutorials

## Installation

### Prerequisites

1. **LibreOffice 26.x** installed on your system. On Windows, the standard path is
   `C:\Program Files\LibreOffice\program\soffice.exe`. On Linux/macOS, `soffice`
   should be on your PATH. If LibreOffice is installed in a non-standard location,
   set the `LIBREOFFICE_MCP_SOFFICE_PATH` environment variable.

2. **Python 3.12+** with `uv` (Astral package manager). Install from
   [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/).

3. **Ollama** (optional) for agentic workflow features. Install from
   [https://ollama.com](https://ollama.com), then pull a model:
   `ollama pull qwen3.5:27b` or `ollama pull gemma3:12b`.

### Claude Desktop Setup

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "libreoffice-mcp": {
      "command": "python",
      "args": ["-m", "libreoffice_mcp.server", "--stdio"],
      "env": {
        "PYTHONPATH": "${PWD}/src",
        "PYTHONUNBUFFERED": "1",
        "LIBREOFFICE_MCP_SOFFICE_PATH": "C:\\Program Files\\LibreOffice\\program\\soffice.exe"
      }
    }
  }
}
```

Or use the `.mcpb` bundle with `mcpb install`.

### Cursor Setup

Add to your Cursor MCP configuration (`.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "libreoffice-mcp": {
      "command": "python",
      "args": ["-m", "libreoffice_mcp.server", "--stdio"],
      "env": {
        "PYTHONPATH": "/path/to/libreoffice-mcp/src",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### HTTP Mode (Webapp Dashboard)

To run the full stack with webapp dashboard:

```powershell
# Clone and install
git clone https://github.com/sandraschi/libreoffice-mcp
cd libreoffice-mcp
uv sync
cd webapp
bun install

# Start backend + frontend
just webapp
```

The backend starts on port 10981, the frontend on port 10983. Open
`http://127.0.0.1:10983` in your browser.

### Extension Bridge (Optional — Live Writer/Calc)

To use live Writer typewriter, Calc cell manipulation, and UNO macro execution:

1. Install the `libreoffice-mcp-bridge.oxt` extension in LibreOffice
   (Tools → Extension Manager → Add)
2. Restart LibreOffice — the bridge auto-starts on port 8765
3. Verify: `libreoffice(operation="bridge_discover")` should return `"online": true`

Without the bridge, you can still use all headless operations (convert, merge,
batch_pack, pdf_merge, watch_folder, read_spreadsheet).

---

## Tutorial 1: Your First Document Conversion

Let's convert a markdown file to PDF. This is the most common operation.

### Step 1: Check the server is healthy

```
libreoffice(operation="status")
```

Expected response: `soffice_found: true`, `soffice_path` set, version shown. If
`soffice_found` is false, set the env var or check your LibreOffice installation.

### Step 2: Inspect your document (optional)

```
libreoffice(operation="document_info", input_path="C:/Users/sandr/Documents/report.md")
```

This tells you the document family ("writer"), its size, and suggested output formats
(`["pdf", "docx", "odt", "html", "txt", "rtf"]`).

### Step 3: Convert to PDF

```
libreoffice(operation="convert", input_path="C:/Users/sandr/Documents/report.md", output_format="pdf")
```

The server renders the markdown to HTML (with headings, formatting, tables, code blocks),
then converts through LibreOffice to a styled PDF. The response includes the output path.

### Step 4: Open in Windows Explorer

```
libreoffice(operation="reveal_output", input_path="report.pdf")
```

This opens the output directory in Explorer, highlighting the file.

### Alternative: Convert to DOCX

```
libreoffice(operation="convert", input_path="C:/Users/sandr/Documents/report.md", output_format="docx")
```

LibreOffice handles the markdown→HTML→DOCX pipeline identically. You can open the result
in Microsoft Word or LibreOffice Writer.

### Batch conversion

To convert an entire folder of markdown files at once:

```
libreoffice(operation="convert_batch", input_paths=[
    "C:/docs/chapter1.md",
    "C:/docs/chapter2.md",
    "C:/docs/chapter3.md"
], output_format="pdf")
```

Each file is converted independently. Check the `results` array for per-file status.
Failures on individual files don't stop the batch.

---

## Tutorial 2: Template Merge — Creating a Fleet Report

LibreOffice MCP ships with three bundled ODT templates using `{{PLACEHOLDER}}` syntax.
This tutorial creates a weekly report.

### Step 1: List available templates

```
libreoffice(operation="list_templates")
```

You'll see three entries: `fleet-report.odt`, `fleet-board-pack.odt`, `fleet-artifact-pack.odt`.
Each lists its required placeholders.

### Step 2: Fill the template

```
libreoffice(operation="merge", template="fleet-report.odt", placeholders={
    "TITLE": "Weekly Fleet Status — June 23, 2026",
    "DATE": "2026-06-23",
    "SUMMARY": "All 42 fleet MCP servers operational. 3 PRs merged. 0 incidents.",
    "BODY": "## Backend Services\n\nAll services healthy. Port reservoir: 0 conflicts.\n\n## Frontend Apps\n\nAll Vite dashboards loading. No console errors on audit.\n\n## CI/CD\n\n- github-actions: 12/12 passing\n- fleet-cold-install-probe: 38/38 passing\n\n## Action Items\n\n- Upgrade FastMCP to 3.4.x in repos still on 3.2.x\n- Add Prefab cards to documentation-mcp"
})
```

### Step 3: Get the PDF

The `output_format` defaults to `"pdf"`, so this automatically creates both the merged
ODT and the final PDF. The response includes:
- `merged_odt` — path to the intermediate ODT
- `output` — path to the final PDF

### Rich BODY Content

The `BODY` placeholder supports markdown. The server converts markdown headings, bold,
italic, and lists to ODF XML before inserting. This means your report body can have
proper document structure — not just flat text.

For the `KPI_TABLE` placeholder in board packs, use pipe tables:

```
| KPI | Value | Target | Status |
|---|---|---|---|
| Servers Healthy | 42/42 | 42/42 | OK |
| Avg Latency | 45ms | <100ms | OK |
| Error Rate | 0.1% | <1% | OK |
```

The markdown table renders as formatted text with proper column alignment.

### Custom Templates

You can use your own ODT templates. Just place them in `data/libreoffice-mcp/templates/`
and reference by filename:

```
libreoffice(operation="merge", template="my-custom-template.odt", placeholders={
    "NAME": "Sandra Schipal",
    "DATE": "2026-06-23"
})
```

The template must contain `{{KEY}}` placeholders in its `content.xml`. Create your
template in LibreOffice Writer, save as ODT, then place in the templates directory.

---

## Tutorial 3: Batch Markdown Pack

Combine multiple markdown files into one polished PDF document.

### Scenario

You have three markdown files from different fleet services and want a single PDF report:
- `C:/reports/browser-mcp.md` — browser automation status
- `C:/reports/email-mcp.md` — email service health
- `C:/reports/calibre-mcp.md` — library stats

### The command

```
libreoffice(operation="batch_pack", input_paths=[
    "C:/reports/browser-mcp.md",
    "C:/reports/email-mcp.md",
    "C:/reports/calibre-mcp.md"
], pack_title="Fleet Services Report — June 2026", output_stem="fleet-services-june")
```

The output is a single PDF with:
- Title page: "Fleet Services Report — June 2026"
- Section for each file: `## {filename}` as H2 heading, followed by the markdown content
- `---` separators between sections

You can also output to HTML or markdown by changing `output_format`:

```
libreoffice(operation="batch_pack", ..., output_format="html")
```

Returns an HTML file with the same structure but no LibreOffice conversion step.

---

## Tutorial 4: PDF Merge

Combine multiple existing PDFs into one file.

```
libreoffice(operation="pdf_merge", input_paths=[
    "C:/docs/cover-page.pdf",
    "C:/docs/report-body.pdf",
    "C:/docs/appendix.pdf"
], output_stem="complete-report")
```

All inputs must be valid PDF files. Uses `pypdf.PdfWriter` for concatenation (no
LibreOffice dependency for this operation). The order of `input_paths` determines
the page order in the output.

---

## Tutorial 5: Folder Watch — Auto-Convert Pipeline

Set up a background watcher that automatically converts new files dropped into a folder.

### Start watching

```
libreoffice(operation="watch_start", watch_path="C:/Users/sandr/Desktop/to-convert", watch_glob="*.md", output_format="pdf")
```

Now, any new `.md` file saved to `C:/Users/sandr/Desktop/to-convert/` is automatically
converted to PDF. The watcher polls every few seconds, tracks file modification times,
and skips already-processed files.

### Check status

```
libreoffice(operation="watch_status")
```

Returns the watch path, glob pattern, format, running state, and count of files processed.

### Stop watching

```
libreoffice(operation="watch_stop")
```

The watcher is a daemon thread — it stops when the MCP server stops, but explicit
`watch_stop` gives you a clean shutdown with final stats.

### Use case

Perfect for automated pipelines where another tool or script writes files to a folder
and you want them automatically converted to PDF for distribution or archival.

---

## Tutorial 6: Live Writer Typewriter (Extension Bridge Required)

With the extension bridge installed, you can stream text into a running LibreOffice
Writer instance.

### Step 1: Launch Writer

```
libreoffice(operation="launch_writer")
```

If the bridge is online, this connects to the existing Writer instance. If not, it
starts a new LibreOffice Writer window.

### Step 2: Check session

```
libreoffice_writer(operation="status")
```

Confirms the bridge is connected and Writer is ready to receive text.

### Step 3: Stream AI-generated content

```
libreoffice(operation="live_write", prompt="Write a one-page summary of the SOTA 2026 fleet standards covering FastMCP 3.3, portmanteau pattern, Prefab UI, and coworker PDF flows", typewriter_wpm=60, max_words=500)
```

The server uses the configured LLM (Ollama or client-side sampling) to generate text,
then streams it character-by-character into the Writer document at the specified speed.
It looks like a human typing — useful for demos and screen recordings.

### Step 4: Type specific text

```
libreoffice(operation="live_type", live_text="## Action Items\n\n1. Review PR #42\n2. Update INSTALL.md for all repos\n3. Run fleet cold-install probe")
```

Injects predefined text at the current cursor position, with the typewriter effect.

### Step 5: Run a UNO macro

```
libreoffice(operation="run_macro", macro_name="Standard.Module1.FormatReport", macro_language="Basic", macro_location="document")
```

Executes a registered UNO macro in the open document. Useful for applying formatting,
running calculations, or triggering custom automation.

### Fallback mode

If the extension bridge is offline and `headless_fallback=true`:
- `live_write` generates an ODT via headless conversion and opens it in Writer
- `live_type` does the same
- `run_macro` returns an error (macros require the live bridge)

---

## Tutorial 7: Live Calc Pivot Demo (Extension Bridge Required)

This is the showcase Calc operation: seed a spreadsheet, then create a pivot table.

### Step 1: Check Calc bridge

```
libreoffice_calc(operation="status")
```

### Step 2: Run the pivot demo

```
libreoffice_calc(operation="live_pivot_demo", source_range="A1:D7", row_field="Region", data_field="Revenue", pivot_name="SalesByRegion", typewriter_seed=true)
```

What happens:
1. A new Calc spreadsheet opens (or the existing one is used)
2. Demo data is typed into cells with the typewriter effect:
   - Region, Product, Quarter, Revenue columns
   - 6 rows of sales data
3. A Data Pilot pivot table is created summing Revenue by Region
4. The pivot is placed at row 9, column 0

### Step 3: Type custom cells

```
libreoffice_calc(operation="type_cells", cells=[
    {"row": 0, "col": 0, "value": "Department"},
    {"row": 0, "col": 1, "value": "Headcount"},
    {"row": 0, "col": 2, "value": "Budget"},
    {"row": 1, "col": 0, "value": "Engineering"},
    {"row": 1, "col": 1, "value": 12},
    {"row": 1, "col": 2, "value": 2400000},
    {"row": 2, "col": 0, "value": "Design"},
    {"row": 2, "col": 1, "value": 4},
    {"row": 2, "col": 2, "value": 800000}
], delay_sec=0.1)
```

Types each cell with a small delay for the typewriter effect.

### Step 4: Read a spreadsheet file

```
libreoffice(operation="read_spreadsheet", input_path="C:/data/fleet-budget.ods")
```

Returns sheet names, headers, and data rows without opening Calc. Works with `.ods`,
`.xlsx`, `.xls`, and `.csv` files.

---

## Tutorial 8: Agentic Workflow — Autonomous Document Tasks

Use natural language to orchestrate multi-step document operations.

### Prerequisites

Ensure Ollama is running with a model pulled:

```powershell
ollama serve
ollama pull qwen3.5:27b
```

Set environment variables:
```
LIBREOFFICE_MCP_SAMPLING_BASE_URL=http://127.0.0.1:11434/v1
LIBREOFFICE_MCP_SAMPLING_MODEL=qwen3.5:27b
```

Or use client-side sampling:
```
LIBREOFFICE_MCP_SAMPLING_USE_CLIENT_LLM=1
```

### Example 1: Check status and list resources

```
libreoffice_agentic_workflow(goal="Check soffice status, list all templates, and discover the extension bridge")
```

The LLM plans three sequential tool calls (lo_status → lo_list_templates →
lo_bridge_discover) and summarizes the results.

### Example 2: Convert and report

```
libreoffice_agentic_workflow(goal="Convert C:/reports/status.md to PDF, then list all templates")
```

The LLM calls lo_convert with the file path, waits for success, then calls
lo_list_templates to show what's available.

### Example 3: Generate a coworker report

```
libreoffice_agentic_workflow(goal="Create a weekly fleet report titled 'Fleet Status June 23'. Use the fleet-report.odt template. Set DATE to 2026-06-23, SUMMARY to 'All systems nominal. 42 of 42 servers healthy. Zero incidents this week.' and BODY to a brief paragraph about the CI pipeline passing all tests.")
```

The LLM identifies this as a merge operation, fills the placeholders, and executes
`lo_merge` with the correct template and values.

### Example 4: Batch pack with discovery

```
libreoffice_agentic_workflow(goal="Check what templates are available, then combine C:/docs/intro.md and C:/docs/conclusion.md into a PDF called 'Project Summary'")
```

The LLM first discovers templates (to confirm the environment), then calls lo_batch_pack.

### When to use agentic

- When the task involves multiple steps that depend on each other
- When you don't remember the exact parameter names
- When you're exploring what's available before committing to an operation
- For complex coworker report generation with rich body content

### When to use direct tools

- Single-step operations (just convert one file)
- When you know exactly which operation and parameters you need
- For performance-critical scenarios (agentic adds LLM latency)

---

## Tutorial 9: Extension Bridge — Discover and Proxy Tools

### Discover what the extension exposes

```
libreoffice(operation="bridge_discover")
```

If the bridge is online, you'll see something like:
```json
{
  "online": true,
  "url": "http://127.0.0.1:8765/mcp",
  "tool_count": 8,
  "tools": [
    {"name": "writer_insert_text", "description": "Insert text at cursor position"},
    {"name": "writer_get_content", "description": "Read current document content"},
    ...
  ]
}
```

### Proxy a tool call

```
libreoffice(operation="bridge_call", bridge_tool="writer_insert_text", bridge_arguments={"text": "Hello from the fleet!"})
```

This forwards the call to the extension bridge and returns the response. Use this to
access extension-specific tools that aren't directly exposed in the main ToolSet.

### Use case

The extension bridge is the gateway to live Writer/Calc manipulation. MCP extensions
like WriterAgent or mcp-libre expose their own tools (text insertion, formatting,
document navigation, etc.). `bridge_discover` lets you see what's available, and
`bridge_call` lets you use any of them.

---

## Tutorial 10: Prefab Cards — Rich In-Chat UI

Two Prefab cards provide quick visual status without parsing JSON:

### Status Card

```
show_libreoffice_status_card()
```

In supporting MCP clients (Claude Desktop, Cursor with Prefab support), this renders
a visual card showing:
- soffice icon with version and path
- Extension bridge status with online/offline badge
- Writer and Calc bridge connection states
- Tool count summary

In clients without Prefab support, it falls back to a plain-text summary.

### Templates Card

```
show_templates_card()
```

Renders a gallery card of bundled templates with:
- Template name and description
- Placeholder key list
- Clickable file paths

Use these as the first call in any conversation about LibreOffice to get an immediate
visual overview.

---

## Troubleshooting

### "soffice not found"

**Symptom**: `libreoffice(operation="status")` returns `soffice_found: false`.

**Fix**: Set `LIBREOFFICE_MCP_SOFFICE_PATH` to the absolute path of your soffice binary.
On Windows it's typically `C:\Program Files\LibreOffice\program\soffice.exe`. Verify:
```powershell
Test-Path "C:\Program Files\LibreOffice\program\soffice.exe"
```

### "Extension bridge offline"

**Symptom**: `bridge_discover` returns `"online": false` with an error about connection
refused or timeout.

**Fix**: This is expected if you haven't installed the extension bridge `.oxt`.
Headless operations (convert, merge, batch_pack, pdf_merge, watch) all work without it.
Only live Writer/Calc and macro features need the bridge. To install:
1. Open LibreOffice
2. Tools → Extension Manager → Add
3. Select `dist/libreoffice-mcp-bridge.oxt`
4. Restart LibreOffice

### "Conversion timed out"

**Symptom**: A convert operation returns with `error: "Conversion timed out after 120s"`.

**Fix**: Large documents (50+ pages, many images) can take longer. Options:
- Use `queue_job=true` to run as a background job (trackable in the webapp)
- Split the document into smaller sections and batch-convert
- The timeout is configurable in `settings.convert_timeout_sec`

### "Expected output missing"

**Symptom**: `convert` returns success false with "Expected output missing".

**Fix**: LibreOffice sometimes produces output with a different filename than expected.
The server tries fuzzy matching (checking for recently-modified files with the same stem).
If this fails, check the output directory manually:
```powershell
Get-ChildItem data/libreoffice-mcp/output/ | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```

### "Sampling failed" / Agentic workflow errors

**Symptom**: `libreoffice_agentic_workflow` returns an error about sampling.

**Fix**: 
- Server-side: ensure Ollama is running and has a model pulled:
  ```powershell
  ollama serve
  ollama pull qwen3.5:27b
  ```
- Client-side: set `LIBREOFFICE_MCP_SAMPLING_USE_CLIENT_LLM=1` if your MCP client
  supports sampling (Claude Desktop and Cursor do)
- If neither works, `ssh localhost` to check Ollama, or run
  `curl http://127.0.0.1:11434/api/tags` to verify model availability

### "pypdf not installed" (pdf_merge)

**Symptom**: `pdf_merge` returns "pypdf not installed".

**Fix**: Run `uv sync` in the repo root. `pypdf` is a core dependency and should be
installed automatically with `uv sync`.

### Template merge produces garbled output

**Symptom**: Merged document has missing or garbled placeholder content.

**Fix**: 
- Ensure placeholder keys in the template exactly match your dict keys (case-sensitive,
  uppercase by convention: `TITLE` not `title`)
- Only `content.xml` and `meta.xml` are processed — placeholders in `styles.xml` are
  not substituted
- Rich content (BODY, NARRATIVE, ACTION_ITEMS) supports markdown; if markdown is not
  rendering correctly, try plain text values instead

### Watch folder not picking up files

**Symptom**: Files placed in the watch folder are not being converted.

**Fix**:
- Check `libreoffice(operation="watch_status")` to confirm the watcher is running
- The watcher excludes `.tmp`, `.partial`, and `.db` files — rename if needed
- The watcher tracks files by modification time; if a file was created before the
  watcher started with no new modifications, it won't be processed. Touch the file
  to update its mtime.
- Check the server logs (visible in the webapp Logs page) for any watcher errors

### Port conflicts (10981 / 10983)

**Symptom**: HTTP mode fails to start with "address already in use".

**Fix**: These ports are registered in the fleet port registry. Check if another
process is using them:
```powershell
Get-NetTCPConnection -LocalPort 10981 -ErrorAction SilentlyContinue
Get-NetTCPConnection -LocalPort 10983 -ErrorAction SilentlyContinue
```
Kill any stale processes before restarting.

---

## Quick Reference: Common Command Patterns

### Convert a single file
```
libreoffice(operation="convert", input_path="C:/path/to/file.md")
libreoffice(operation="convert", input_path="C:/path/to/file.docx", output_format="pdf")
libreoffice(operation="convert", input_path="C:/path/to/file.odt", output_format="docx")
```

### Inspect before converting
```
libreoffice(operation="document_info", input_path="C:/path/to/file.xlsx")
```

### Generate a fleet report
```
libreoffice(operation="merge", template="fleet-report.odt", placeholders={"TITLE": "...", "DATE": "...", "SUMMARY": "...", "BODY": "..."})
```

### Combine markdown files into one PDF
```
libreoffice(operation="batch_pack", input_paths=["a.md", "b.md", "c.md"], pack_title="My Pack")
```

### Merge PDFs
```
libreoffice(operation="pdf_merge", input_paths=["a.pdf", "b.pdf"], output_stem="combined")
```

### Auto-convert a folder
```
libreoffice(operation="watch_start", watch_path="C:/incoming", watch_glob="*.md")
```

### Read a spreadsheet without opening Calc
```
libreoffice(operation="read_spreadsheet", input_path="C:/data/budget.xlsx")
```

### Show visual status card
```
show_libreoffice_status_card()
```

### Show template gallery
```
show_templates_card()
```

### Agentic multi-step task
```
libreoffice_agentic_workflow(goal="List templates, then create a board pack with Q3 KPIs")
```

---

## Example Conversations

### Conversation 1: New User Setup

> **User**: I just installed LibreOffice MCP. How do I get started?

**Assistant**: Let's check the server health first.
```
libreoffice(operation="status")
```
[Assistant reads the response]

Your soffice is detected at `C:\Program Files\LibreOffice\program\soffice.exe`,
version 26.2.3.2. The extension bridge is offline (that's fine — you don't need it
for basic operations). Here's what you can do right now:

1. Convert a document: `libreoffice(operation="convert", input_path="C:/path/to/file.md")`
2. List templates: `libreoffice(operation="list_templates")`
3. Show visual status: `show_libreoffice_status_card()`

What kind of document work do you need to do?

### Conversation 2: Coworker PDF Workflow

> **User**: I need to generate a weekly board pack for the fleet review meeting.

**Assistant**: Let me first check what templates are available.
```
show_templates_card()
```
[Assistant reviews the card]

We have `fleet-board-pack.odt` with placeholders: TITLE, DATE, KPI_TABLE, NARRATIVE,
ACTION_ITEMS. What are your KPIs for this week?

> **User**: All 42 servers are healthy. CI pipeline is green. 3 PRs merged.

**Assistant**: Let me build the board pack with those metrics.
```
libreoffice(operation="merge", template="fleet-board-pack.odt", placeholders={
    "TITLE": "Fleet Board Pack — Week of June 23, 2026",
    "DATE": "2026-06-23",
    "KPI_TABLE": "| KPI | Value | Target | Status |\n|---|---|---|---|\n| Healthy Servers | 42/42 | 42/42 | OK |\n| CI Pipeline | Green | Green | OK |\n| PRs Merged | 3 | — | OK |\n| Incidents | 0 | 0 | OK |",
    "NARRATIVE": "This week the fleet maintained full operational status across all 42 MCP servers. The CI pipeline passed all tests including the cold-install probe (38/38). Three pull requests were merged: FastMCP bump in email-mcp, Prefab card additions to documentation-mcp, and a CORS fix in calibre-mcp.",
    "ACTION_ITEMS": "- Upgrade FastMCP to 3.4.x in remaining 12 repos\n- Add CUA-NSIS smoke tests to notebooklm-fleet-mcp\n- Review and merge the arxiv-mcp epistemic job PR"
})
```
[Assistant reads the response]

The board pack has been generated. The PDF is at `data/libreoffice-mcp/output/merged-{id}.pdf`.
Would you like me to reveal it in Explorer?

### Conversation 3: Batch Processing

> **User**: I have 20 markdown files in C:/reports/. I want them all as PDFs and then
> combined into one document.

**Assistant**: Let's do this in two steps. First, batch convert all 20 files.
```
libreoffice(operation="convert_batch", input_paths=[...], output_format="pdf")
```
[Assistant lists the 20 paths]

Now let's combine them into one PDF. Since they're already individual PDFs, we'll use
pdf_merge:
```
libreoffice(operation="pdf_merge", input_paths=[...], output_stem="all-reports-combined")
```
[Assistant reads and reports]

Done! 20 individual PDFs were created, then merged into one combined file:
`data/libreoffice-mcp/output/all-reports-combined.pdf`

### Conversation 4: Live Writer Demo

> **User**: Can you demonstrate the live Writer typewriter feature?

**Assistant**: Let me check if the extension bridge is connected.
```
libreoffice_writer(operation="status")
```
[Assistant reads the status]

The bridge is online. Writer is connected. Let me generate a short document about
the fleet architecture and stream it into Writer:

```
libreoffice(operation="live_write", prompt="Write a 300-word overview of the Antigravity SOTA fleet architecture covering FastMCP 3.3, the portmanteau pattern, Prefab UI cards, and the coworker PDF pipeline", typewriter_wpm=70, max_words=300)
```

Watch your LibreOffice Writer window — text should appear character by character
as if being typed.

---

## Webapp Dashboard Quick Tour

### Dashboard Page
Shows live health metrics: soffice status, version, bridge connectivity, output count.
Green/red status indicators with `data-testid` attributes for automated testing.

### Simple Actions Page
Form-based interface for the three most common operations:
- **Convert**: File picker → format selector → convert button. Shows conversion
  result with download link.
- **Merge**: Template selector → placeholder form fields → merge button.
- **Batch Pack**: Multi-file selector → title input → pack button.

### Workflows Page
Dedicated forms for the three coworker PDF flows:
- **Weekly Report**: Pre-filled TITLE/DATE/SUMMARY/BODY form → generates fleet-report PDF
- **Board Pack**: KPI table editor + narrative + action items → fleet-board-pack PDF
- **Artifact Pack**: File selector for multiple markdown files → batch_pack PDF

### Templates Page
Gallery view of all ODT templates with placeholder lists.
Upload custom templates via drag-and-drop.

### Job Queue Page
Live view of background conversion jobs (started with `queue_job=true`).
Shows job status, progress, input/output paths, and errors.

### Chat Page
Direct interaction with the MCP tools. Type tool calls in natural language.
The backend proxies to the tool dispatch with conversational wrapping.

### API Docs Page
Embedded Swagger UI and ReDoc iframes, dark-themed. Direct links to
`http://localhost:10981/docs` and `http://localhost:10981/redoc`.

### Logs Page
Real-time log viewer with filtering by level (INFO, WARNING, ERROR, DEBUG)
and search. Shows conversion logs, bridge events, and watcher activity.

---

## Performance Tips

### Conversion Speed

- Markdown files under 100KB convert in 2-5 seconds
- Large ODT/DOCX files (10MB+) may take 10-30 seconds
- For batch operations, use `queue_job=true` on individual converts to run in parallel
- The `convert_batch` operation runs sequentially — for large batches, use individual
  queued converts instead

### Memory Usage

- LibreOffice headless uses ~200-400MB RAM per conversion
- Batch operations release memory between files
- The watch folder daemon holds minimal memory (~10MB) when idle

### Extension Bridge Latency

- Bridge operations have ~100-200ms network overhead per call
- The typewriter effect adds artificial delay — set `typewriter_wpm` higher for
  faster text injection
- For bulk operations, use headless convert rather than live Writer

### Sampling Performance

- Agentic workflow latency depends on the LLM model size and hardware
- `qwen3.5:27b` on RTX 4090: ~1-3 seconds per reasoning step
- `gemma3:12b`: ~1-2 seconds per step
- Client-side sampling (Claude) has network latency overhead
- For simple tasks, use direct tools instead of agentic workflows

---

## Fleet Architecture Context

LibreOffice MCP is one of 42+ MCP servers in the Antigravity SOTA fleet. It occupies:

| Resource | Value |
|---|---|
| Backend port | 10981 |
| Frontend port | 10983 |
| Extension bridge port | 8765 |
| Data directory | `data/libreoffice-mcp/` |
| Output directory | `data/libreoffice-mcp/output/` |
| Templates directory | `data/libreoffice-mcp/templates/` |

It integrates with the fleet through:
- **Coworker PDF pipeline**: fleet-agent-mcp → libreoffice-mcp (PDF generation)
- **Document conversion**: any fleet MCP → libreoffice-mcp (convert .md/.odt to PDF)
- **Fleet exchange**: output depot accessible by other MCP servers
- **Monitoring**: health endpoint polled by observability-mcp
- **Webapp**: React/Vite SPA following WEBAPP_SOTA_STANDARDS with Apps Hub, dynamic
  tool discovery, and fleet integration

---

## Advanced Workflow Patterns

### Pattern 1: Automated Report Pipeline

Set up an end-to-end pipeline where content is generated by one MCP, converted by
LibreOffice MCP, and delivered by another:

```
1. aiwatcher-mcp generates a markdown digest from RSS feeds
   → outputs: C:/data/digest-20260623.md

2. libreoffice(operation="convert",
   input_path="C:/data/digest-20260623.md")

3. email-mcp attaches the resulting PDF and sends to recipients
```

You can automate this with `@mcp.prompt()` or agentic workflows that chain the tools.

### Pattern 2: Watch-and-Forward Folder

Combine folder watching with another MCP's delivery capability:

```
1. libreoffice(operation="watch_start",
   watch_path="C:/reports/pending",
   watch_glob="*.md")

2. Any markdown file dropped in C:/reports/pending/ is auto-converted to PDF

3. A separate agent reads the output directory and forwards PDFs to their destinations
```

### Pattern 3: Multi-Format Document Generation

Generate the same content in multiple formats for different audiences:

```
# First, create the source markdown
write: C:/reports/status.md

# Convert to PDF for email distribution
libreoffice(operation="convert",
  input_path="C:/reports/status.md",
  output_format="pdf")

# Convert to DOCX for editing in Word
libreoffice(operation="convert",
  input_path="C:/reports/status.md",
  output_format="docx")

# Convert to HTML for web publishing
libreoffice(operation="convert",
  input_path="C:/reports/status.md",
  output_format="html")
```

### Pattern 4: Template-Driven Report Card

Create a library of custom ODT templates for recurring report types:

```
1. Design a template in LibreOffice Writer with {{PLACEHOLDER}} tags
2. Save to data/libreoffice-mcp/templates/
3. Call libreoffice(operation="merge", template="my-template.odt", ...)
4. The template is reusable — just change the placeholder values
```

Common template designs:
- **Invoice**: `{{CLIENT_NAME}}`, `{{INVOICE_NUMBER}}`, `{{DATE}}`, `{{ITEMS_TABLE}}`, `{{TOTAL}}`
- **Certificate**: `{{RECIPIENT}}`, `{{COURSE}}`, `{{DATE}}`, `{{ISSUER}}`
- **Meeting minutes**: `{{MEETING_TITLE}}`, `{{DATE}}`, `{{ATTENDEES}}`, `{{TOPICS}}`, `{{DECISIONS}}`, `{{ACTION_ITEMS}}`
- **Project brief**: `{{PROJECT_NAME}}`, `{{SPONSOR}}`, `{{TIMELINE}}`, `{{BUDGET}}`, `{{SCOPE}}`, `{{RISKS}}`

### Pattern 5: Spreadsheet Data Pipeline

Extract data from spreadsheets for use in other fleet tools:

```
1. libreoffice(operation="read_spreadsheet",
   input_path="C:/data/fleet-inventory.xlsx")
   → Returns structured data: sheets, headers, rows

2. Use the extracted data in another tool:
   - Populate an arr-mcp library report
   - Feed into arxiv-mcp for analysis
   - Send via email-mcp as a structured report
```

### Pattern 6: Agentic Document Assembly

For complex document assembly tasks, let the agentic workflow handle the details:

```
libreoffice_agentic_workflow(goal=
  "Check what templates are available. "
  "Read C:/data/q2-metrics.csv to get numbers. "
  "Create a board pack from fleet-board-pack.odt using those numbers as KPIs. "
  "Add a narrative about fleet performance. "
  "List three action items for the next quarter."
)
```

The LLM will:
1. Call lo_list_templates to confirm templates
2. Call lo_status to verify soffice
3. Parse the CSV data (you'd need to provide it in the goal)
4. Call lo_merge with the right placeholders
5. Report the output path

---

## Understanding the Output Depot

Every successful conversion is indexed in the output depot, which maintains a JSON log
of recent conversions at `data/libreoffice-mcp/output/.index.json`. Each entry records:

- `input`: source file path
- `output`: converted file path
- `format`: target format
- `family`: document family
- `timestamp`: conversion time
- `size_bytes`: output file size

The webapp Output page displays this index in a sortable, filterable table with download
links. Files persist in the output directory until manually cleaned up.

To access converted files from other MCP tools:
```
# List recent conversions
GET /api/v1/output

# Download a specific file
GET /api/v1/download/{filename}
```

---

## Configuration Reference

### Full Environment Variable Reference

| Variable | Default | Description |
|---|---|---|
| `LIBREOFFICE_MCP_SOFFICE_PATH` | Auto-detect | Override soffice binary path |
| `LIBREOFFICE_MCP_EXTENSION_BRIDGE_URL` | `http://127.0.0.1:8765/mcp` | Extension MCP bridge URL |
| `LIBREOFFICE_MCP_SAMPLING_BASE_URL` | `http://127.0.0.1:11434/v1` | Sampling API endpoint |
| `LIBREOFFICE_MCP_SAMPLING_MODEL` | `qwen3.5:27b` | Model for server-side sampling |
| `LIBREOFFICE_MCP_SAMPLING_USE_CLIENT_LLM` | `0` | Use host client LLM for sampling |
| `LIBREOFFICE_MCP_PREFAB_APPS` | `1` | Enable/disable Prefab card tools |
| `LIBREOFFICE_MCP_PORT` | `10981` | HTTP server bind port |
| `LIBREOFFICE_MCP_HOST` | `127.0.0.1` | HTTP server bind host |
| `LIBREOFFICE_MCP_OUTPUT_DIR` | `data/libreoffice-mcp/output` | Override output directory |
| `LIBREOFFICE_MCP_TEMPLATES_DIR` | `data/libreoffice-mcp/templates` | Override templates directory |
| `LIBREOFFICE_MCP_CONVERT_TIMEOUT` | `120` | Conversion timeout in seconds |
| `LIBREOFFICE_MCP_WATCH_POLL_SEC` | `5` | Watch folder poll interval |

### LibreOffice Version Requirements

- **Minimum**: LibreOffice 7.6
- **Recommended**: LibreOffice 26.2 or later
- **Known working**: LibreOffice 26.2.3.2 (fleet-tested)
- **Headless mode**: All versions support `soffice --headless --convert-to`
- **Extension bridge**: Requires LibreOffice 7.6+ with Python UNO support

### Supported Operating Systems

- **Windows 10/11**: Primary target. Fleet-tested on Windows 11 with LibreOffice 26.2.3.2
- **Linux**: Supported via `soffice` binary. Auto-detection scans common paths
- **macOS**: Supported. `soffice` typically at `/Applications/LibreOffice.app/Contents/MacOS/soffice`

---

## Keyboard Shortcuts & Quick Reference

When using the webapp dashboard:

| Shortcut | Page | Action |
|---|---|---|
| `Ctrl+1` | Dashboard | Go to dashboard |
| `Ctrl+2` | Simple Actions | Go to convert/merge forms |
| `Ctrl+3` | Workflows | Go to coworker PDF workflows |
| `Ctrl+4` | Templates | Go to template gallery |
| `Ctrl+5` | Jobs | Go to job queue |
| `Ctrl+6` | Chat | Go to MCP chat |
| `Ctrl+Scroll` | Any | Zoom UI (persisted to localStorage) |

When using MCP tools in Claude Desktop / Cursor:

| Pattern | Tool |
|---|---|
| Check health | `libreoffice(operation="status")` |
| Show status card | `show_libreoffice_status_card()` |
| Convert file | `libreoffice(operation="convert", input_path="...")` |
| Merge template | `libreoffice(operation="merge", template="...", placeholders={...})` |
| Batch pack | `libreoffice(operation="batch_pack", input_paths=[...], pack_title="...")` |
| Merge PDFs | `libreoffice(operation="pdf_merge", input_paths=[...])` |
| List templates | `libreoffice(operation="list_templates")` |
| Show template card | `show_templates_card()` |
| Watch folder | `libreoffice(operation="watch_start", watch_path="...")` |
| Read spreadsheet | `libreoffice(operation="read_spreadsheet", input_path="...")` |
| Discover bridge | `libreoffice(operation="bridge_discover")` |
| Agentic task | `libreoffice_agentic_workflow(goal="...")` |
| Get help | `libreoffice_help()` or `libreoffice_help(topic="...")`
