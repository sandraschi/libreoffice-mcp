---
name: libreoffice-expert
description: Headless LibreOffice convert, ODT merge, batch pack, and extension bridge operations.
---

# LibreOffice MCP — Operations

Portmanteau tool: `libreoffice(operation=...)`.

## Operations

| Operation | Purpose |
|-----------|---------|
| `status` | soffice path + extension bridge health |
| `convert` | Headless format conversion (.md → HTML → PDF) |
| `merge` | ODT template {{PLACEHOLDER}} → pdf/odt |
| `list_templates` | Bundled fleet ODT templates |
| `batch_pack` | Multiple markdown paths → single PDF |
| `bridge_discover` | List tools on extension MCP :8765 |
| `bridge_call` | Invoke live Writer/Calc extension tool |
| `help` | Capability summary |

## Coworker PDF flows (fleet-agent-mcp)

- `fleet-report.odt` → `coworker_weekly_report_pdf`
- `fleet-board-pack.odt` → `coworker_board_pack`
- `fleet-artifact-pack.odt` → `coworker_artifact_pack`

## Prerequisites

- LibreOffice **26.2+** with `soffice` on PATH or `LIBREOFFICE_MCP_SOFFICE_PATH`
- Optional: WriterAgent / mcp-libre on `:8765/mcp` for live editing

## Agentic

Use `libreoffice_agentic_workflow(goal=...)` for multi-step tasks with sampling (SEP-1577).
Set `LIBREOFFICE_MCP_SAMPLING_BASE_URL` to Ollama OpenAI-compatible endpoint.
