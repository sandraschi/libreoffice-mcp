# libreoffice-mcp — agent instructions

Headless LibreOffice automation (Writer/Calc/Impress convert, ODT merge, batch
packs) + optional live Writer/Calc bridges. Backend :10981, frontend :10983.

## Entry points

- `just install` — uv sync + webapp deps. `just serve` — full stack via start.ps1.
- `just test` — pytest. `just lint` / `just fmt` — ruff + biome. `just certify` — all gates.
- `just pack` — canonical MCPB pipeline (mcpb/pack.ps1: wipe + fresh-copy + checks).
- Server: `src/libreoffice_mcp/server.py` (FastMCP tools) + `api.py` (FastAPI REST).
- Never call bare `mcpb pack` — it ships a stale `mcpb/src` stage.

## Standards

- Fleet bar: `D:\Dev\repos\mcp-central-docs\patterns\repo-assess-and-fix.md`.
- Tool design: Annotated+Field params, `## Return Format` + `## Examples` docstrings,
  `annotations=` on every tool, dialogic `{success, message, data}` returns.
- No bare `except:`, no `print()` in src (T20 enforced), no S110/S112 ignores.
- PowerShell 5.1 only (`scripts/Test-Ps51Parse.ps1` gate); just recipes join
  `Set-Location` with `;` — never a bare `Set-Location` line (wrong-directory runs).

## Key files

- `fleet-start.config.ps1` — ports + backend target (edit here, not start.ps1).
- `pyproject.toml` — ruff select (keep T20), pytest-cov config, dev extras.
- `glama.json` — tools array must match the 7 registered MCP tools.
- `docs/ONBOARDING.md` — wrappee/account setup (LibreOffice + optional LLM keys).
- Session prompts: `.cursorrules` / `hooks/hooks.json` / `.opencode/skills/` /
  `.agents/skills/` — concrete tool names only; audit after any tool rename.

## Session Context (LibreOffice MCP)

Headless LibreOffice automation: convert, ODT merge, batch packs, live Writer/Calc.

**Before starting work:**
1. Check server health: libreoffice(operation="status")
2. List templates for merge flows: libreoffice(operation="list_templates")

**At end of work, save deliverables:**
- Export artifacts via convert/merge; reveal outputs with libreoffice(operation="reveal_output")
