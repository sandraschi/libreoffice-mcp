# Troubleshooting

## soffice not found

LibreOffice must be installed on the host — libreoffice-mcp does not bundle it. See [LIBREOFFICE.md](LIBREOFFICE.md) and [INSTALL.md](../INSTALL.md).

Set `LIBREOFFICE_MCP_SOFFICE_PATH` in `.env` or the Settings page.

Windows default: `C:\Program Files\LibreOffice\program\soffice.exe`

Verify: `GET /health` → `soffice_available: true`, or run the **Tests** page in the webapp.

## Dashboard won't start

```powershell
just bootstrap-web
just webapp
```

Check ports **10981** (backend) and **10983** (webapp) are free.

## npm install hangs

Use `scripts/bootstrap-webapp.ps1` (`.npmrc` with `legacy-peer-deps`).

## Extension bridge offline

Normal if WriterAgent/mcp-libre is not running. Headless convert, merge, batch, and PDF merge still work.

Install the extension, enable MCP on port **8765**.

## Convert / merge job errors

Check the **Logs** or **Jobs** page. Common causes:

- Missing input path or unsupported format
- `soffice` timeout — increase `LIBREOFFICE_MCP_CONVERT_TIMEOUT_SEC`
- Invalid ODT template placeholders

Job details include stderr from `soffice` when available.

## Upload fails

- File exceeds `LIBREOFFICE_MCP_MAX_UPLOAD_BYTES` (default 50 MB)
- Disk full under `UPLOAD_DIR` (`~/.libreoffice-mcp/uploads`)

## Folder watch not converting

- Confirm `watch_status` shows the folder active
- Only supported extensions are converted (see **Formats** API or docs/FEATURES.md)
- Poll interval: `LIBREOFFICE_MCP_WATCH_POLL_SEC`

## PDF merge errors

Requires readable PDF inputs. Corrupt or encrypted PDFs fail with pypdf error in job result.

## Apps Hub empty

Verify `LIBREOFFICE_MCP_CENTRAL_DOCS_PATH` points at `mcp-central-docs` with `operations/webapp-registry.json`.

## Chat / agentic planner

The **Chat** page uses the built-in agentic planner (`POST /api/chat`), not raw Ollama by default.

For sampling enrichment in MCP agentic workflows, start Ollama or set `LIBREOFFICE_MCP_SAMPLING_BASE_URL`.

## SQLite / jobs persistence

Jobs and output index live in `~/.libreoffice-mcp/data/libreoffice-mcp.db`. Delete the file only if you want to reset history.

## Native Tauri build

LibreOffice is **not** bundled in the desktop installer — install LO separately on each machine.
