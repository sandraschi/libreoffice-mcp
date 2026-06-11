# libreoffice-mcp

General-purpose LibreOffice automation for agents and humans — headless **Writer, Calc, and Impress** conversion, ODT template merge, PDF combine, folder watch, **live Writer typewriter**, and optional extension MCP.

**Version 0.3.0** · [INSTALL.md](INSTALL.md) · [docs/FEATURES.md](docs/FEATURES.md) · [docs/LIVE_WRITER.md](docs/LIVE_WRITER.md) · [docs/EXTENSION_CALC_BRIDGE.md](docs/EXTENSION_CALC_BRIDGE.md) · [docs/COMPARISON-OTHER-LO-MCP.md](docs/COMPARISON-OTHER-LO-MCP.md)

## How it runs

| Mode | Host app | When |
|------|----------|------|
| **Headless (default)** | `soffice --headless` | Convert, merge, batch, PDF merge — no GUI |
| **Live Writer (optional)** | Writer + **libreoffice-mcp-bridge.oxt** | Auto-start bridge; watch typing + UNO macros |
| **Live Calc (optional)** | Calc + **libreoffice-mcp-calc-bridge.oxt** | Cell typewriter + Data Pilot pivot in GUI |
| **Extension bridge (optional)** | Live LO + WriterAgent/mcp-libre | In-app UNO tools on `:8765` |

> **Headless by default** — most tools spawn headless `soffice` automatically. **Open Writer + run the bridge macro** only when you want to *watch* live typing. LibreOffice must be installed — [INSTALL.md](INSTALL.md).

## Hands-in / Hands-out

| Direction | Artifacts | Notes |
|-----------|-----------|-------|
| **Hands-in** | Natural-language prompts | `live_write`, Chat, agentic planner |
| **Hands-in** | `.md`, `.docx`, `.odt`, `.xlsx`, `.pptx`, uploads | Convert, merge, batch |
| **Hands-in** | ODT templates + `{{PLACEHOLDERS}}` | Rich markdown in BODY fields |
| **Hands-out** | `.pdf`, `.docx`, `.odt`, `.xlsx`, `.html` | Headless export |
| **Hands-out** | Live Writer document | Typewriter session — watch GUI update |
| **Hands-out** | Merged PDF packs | Fleet coworker flows still supported |

### Fleet pipelines (downstream)

| Downstream | Takes from libreoffice-mcp |
|------------|----------------------------|
| Email / fleet-agent | PDF reports, board packs |
| Immich / OCR | Scanned PDFs → text via convert |
| Calibre | EPUB/HTML via convert pipeline |

## Ports

| Service | Port |
|---------|------|
| Backend (HTTP `/mcp` + REST) | **10981** |
| Webapp dashboard | **10983** |
| Extension MCP bridge | **8765** |

## Quick start

```powershell
just install
just webapp
```

Open **http://127.0.0.1:10983**. For **live write**: see [docs/LIVE_WRITER.md](docs/LIVE_WRITER.md).

## What you can do

- **Live write** — prompt → watch Writer type (SSE + typewriter panel)
- **Convert** — ODT, DOCX, PDF, XLSX, CSV, PPTX, HTML, MD → any supported export
- **Merge** — ODT templates with `{{PLACEHOLDERS}}`
- **Batch / PDF merge / folder watch / upload / agentic chat**

## MCP tool

`libreoffice(operation=…)` — full reference in [docs/TOOLS.md](docs/TOOLS.md).

## Documentation

| Doc | Audience |
|-----|----------|
| [INSTALL.md](INSTALL.md) | **Install LibreOffice first**, then MCP stack |
| [docs/LIVE_WRITER.md](docs/LIVE_WRITER.md) | Watch-it-write setup |
| [docs/EXTENSION_BRIDGE.md](docs/EXTENSION_BRIDGE.md) | **.oxt** install + UNO macros |
| [docs/LIBREOFFICE.md](docs/LIBREOFFICE.md) | Host app prerequisite |
| [docs/FEATURES.md](docs/FEATURES.md) | Capability overview |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | Environment variables |
| [docs/TOOLS.md](docs/TOOLS.md) | MCP + REST API reference |

## Repo bar

`justfile` · pytest · Biome · Playwright e2e · MCPB · Tauri native · `.env.example`
