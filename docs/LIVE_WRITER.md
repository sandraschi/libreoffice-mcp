# Live Writer (watch it write)

First-class **hands-in / hands-out** live lane — same pattern as [blender-mcp](https://github.com/sandraschi/blender-mcp) session bridge.

## Recommended setup — install the .oxt

**No manual macro.** Build and install the extension:

```powershell
Set-Location D:\Dev\repos\libreoffice-mcp
.\scripts\pack-bridge-oxt.ps1
.\scripts\install-bridge-oxt.ps1
```

Restart LibreOffice. The bridge auto-starts and connects to `:10981`.

Full details: [EXTENSION_BRIDGE.md](EXTENSION_BRIDGE.md)

## What you get

| Mode | Host | Experience |
|------|------|------------|
| **Live GUI (preferred)** | Writer + **libreoffice-mcp-bridge.oxt** | Watch text appear in the document window |
| **Headless fallback** | `soffice --headless` | Generates ODT/PDF and opens Writer when bridge offline |

**Hands-in:** `"Write a short story about butterflies"`, or raw text for `live_type`.

**Hands-out:** live `.odt` in Writer, or exported file under `~/.libreoffice-mcp/output/` on fallback.

## Webapp

**Live Write** (`/live-write`):

1. Start `just webapp`
2. Install `.oxt` (above) and restart Writer
3. Prompt → **Watch it write**

## MCP

```python
libreoffice(operation='live_write', prompt='Write a short story about butterflies')
libreoffice(operation='run_macro', macro_name='MyMacro', library='Standard', module='Module1')
libreoffice(operation='list_macros')
```

## REST

| Route | Purpose |
|-------|---------|
| `POST /api/live/write` | Generate + typewriter |
| `GET /api/live/events` | SSE progress |
| `GET /api/v1/writer/pending` | Extension poll |

## Legacy manual macro

Only if you cannot install the extension: `docs/writer_bridge_macro.py` → Run **Main** in Macro dialog.
