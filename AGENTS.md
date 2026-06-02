# libreoffice-mcp Agent Context

Headless LibreOffice MCP — convert, ODT merge, batch pack, extension bridge (:8765).

## Quick ref

```powershell
just              # recipe dashboard
just install      # uv sync + webapp deps
just webapp       # backend :10981 + frontend :10983
just test         # pytest
just lint         # ruff + biome
```

## Ports

| Service | Port |
|---------|------|
| Backend (HTTP `/mcp` + REST) | 10981 |
| Frontend (Vite SOTA webapp) | 10983 |
| Extension bridge (WriterAgent / mcp-libre) | 8765 |

## Architecture

FastMCP 3.3 portmanteau `libreoffice(operation=…)` + `libreoffice_agentic_workflow` (sampling) + prefabs + skills + FastAPI REST + Vite/React dashboard.
Coworker flows (fleet-agent-mcp) use bundled ODT templates for PDF/board/artifact packs.

## Standards

Fleet bar: `INSTALL.md`, `llms.txt`, `llms-full.txt`, `glama.json`, `manifest.json`, `.mcpbignore`, `justfile`, ruff, biome.
FastMCP 3.3: sampling (LIBREOFFICE_MCP_SAMPLING_*), agentic workflow, `@mcp.prompt`, SkillsDirectoryProvider, Prefab apps.
Webapp SOTA: Apps Hub, Chat, Settings, Skills, Logs, API Docs, Simple Actions, Workflows, Tools, Help.
