# Copilot instructions — libreoffice-mcp

Headless LibreOffice automation (convert, ODT merge, batch packs) + live Writer/Calc.
Backend :10981, frontend :10983. Entry points: `just serve`, `just test`, `just certify`.

## Session Context (LibreOffice MCP)

Headless LibreOffice automation: convert, ODT merge, batch packs, live Writer/Calc.

**Before starting work:**
1. Check server health: libreoffice(operation="status")
2. List templates for merge flows: libreoffice(operation="list_templates")

**At end of work, save deliverables:**
- Export artifacts via convert/merge; reveal outputs with libreoffice(operation="reveal_output")
