---
name: coworker-pdf
description: Fritz coworker deliverables — weekly report, board pack, artifact pack via ODT merge.
---

# Coworker PDF workflows

These flows produce styled PDFs for fleet-agent-mcp / Fritz coworker tools.

## Weekly fleet report

1. Gather markdown or structured text for TITLE, DATE, SUMMARY, BODY.
2. `libreoffice(operation='merge', template='fleet-report.odt', placeholders={...}, output_format='pdf')`
3. Or webapp **Workflows → Weekly fleet report**.

## Board pack

Placeholders: TITLE, DATE, KPI_TABLE, NARRATIVE, ACTION_ITEMS.
Template: `fleet-board-pack.odt`.

## Artifact pack

- **Merge path:** `fleet-artifact-pack.odt` with TITLE, DATE, FILE_COUNT, BODY.
- **Batch path:** `batch_pack` with multiple `.md` artifact paths from `.fleet-agent/artifacts/`.

## Output

Files land in `~/.libreoffice-mcp/output/` — preview via webapp **Output** page or REST `/api/output`.
