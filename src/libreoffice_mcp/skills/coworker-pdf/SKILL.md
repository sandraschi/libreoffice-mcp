---
name: coworker-pdf
description: Fritz coworker deliverables — weekly report, board pack, artifact pack via ODT template merge or markdown batch pack.
---

# Coworker PDF deliverables

Styled PDFs for fleet-agent-mcp / Fritz coworker flows: weekly reports, board
packs, artifact packs. Two production paths — **template merge** (branded ODT
layout) or **batch pack** (raw markdown → single PDF). Outputs land in
`~/.libreoffice-mcp/output/` — preview via webapp **Output** page or REST
`GET /api/output`.

## Who should use what

| Caller | Path | When |
|--------|------|------|
| **Agent (you)** | `libreoffice(operation="merge" / "batch_pack")` or the `coworker_*` workflows below | Scheduled/triggered deliverable generation |
| **Human** | Dashboard **Workflows** page (Weekly fleet report, Board pack, Artifact pack) or **Pack** page | One-off packs, visual check before sending |
| **Downstream** | Email / fleet-agent picks up the finished PDF | PDF reports, board packs (see README pipeline table) |

## The three flows

### 1. Weekly fleet report — `fleet-report.odt`

Placeholders: `TITLE`, `DATE`, `SUMMARY`, `BODY` (rich markdown allowed in BODY).

```python
libreoffice(operation="merge", template="fleet-report.odt", output_format="pdf",
            output_stem="weekly-2026-10-04",
            placeholders={"TITLE": "Fleet Weekly", "DATE": "2026-10-04",
                          "SUMMARY": "All stacks green.",
                          "BODY": "## Highlights\n\n- LibreOffice assfix landed\n\n## Next\n\n- Board pack"})
# or the canned workflow:
# run_workflow("coworker_weekly_report_pdf", params={...})
```

### 2. Board pack — `fleet-board-pack.odt`

Placeholders: `TITLE`, `DATE`, `KPI_TABLE`, `NARRATIVE`, `ACTION_ITEMS`.

```python
libreoffice(operation="merge", template="fleet-board-pack.odt", output_format="pdf",
            output_stem="board-pack-2026-10",
            placeholders={"TITLE": "Board Pack", "DATE": "2026-10-04",
                          "KPI_TABLE": "Uptime 99.9% | Deploys 14 | Incidents 0",
                          "NARRATIVE": "## Narrative\n\nSteady quarter.",
                          "ACTION_ITEMS": "- Approve Q4 plan"})
# or: run_workflow("coworker_board_pack", params={...})
```

### 3. Artifact pack — merge path OR batch path

```python
# Merge path (branded): TITLE, DATE, FILE_COUNT, BODY
libreoffice(operation="merge", template="fleet-artifact-pack.odt", output_format="pdf",
            placeholders={"TITLE": "Sprint Artifacts", "DATE": "2026-10-04",
                          "FILE_COUNT": "3", "BODY": "## Contents\n\n- spec.md\n- demo.mp4"})
# Batch path (fast, unbranded): many .md straight to one PDF
libreoffice(operation="batch_pack", input_paths=["a.md", "b.md", "c.md"],
            pack_title="Sprint Artifacts")
# or: run_workflow("coworker_artifact_pack", ...) / run_workflow("batch_markdown_pack", ...)
```

**Which path?** Merge when the recipient expects the branded layout (board,
external stakeholders); batch when speed matters (internal review, archives).
Batch accepts only readable markdown — non-`.md` inputs are skipped.

## End-to-end checklist

1. `libreoffice(operation="list_templates")` — confirm the `.odt` exists (bundled
   templates auto-install on backend start; custom ones go in
   `LIBREOFFICE_MCP_TEMPLATES_DIR`).
2. Gather content per placeholder table above. BODY/NARRATIVE accept markdown
   headings, lists, bold — they render as styled ODF (DocTitle, SectionHeading,
   BodyText).
3. Run `merge` (or `batch_pack`) with `output_stem` set — deterministic filenames
   (`weekly-2026-10-04.pdf`) beat default stems when downstream flows pick files up.
4. Verify: `GET /api/output` lists the file; open it (or `reveal_output`) and
   confirm layout before handing to email/fleet-agent.
5. Track via Jobs page (`queue_job=True` on convert-family ops) when generating
   several packs in one run.

## Troubleshooting

| Symptom | Cause → fix |
|---------|-------------|
| `template required` / template not found | Typo in template name — copy it from `list_templates`; custom templates must live in the templates dir, not an arbitrary path |
| Empty sections in the PDF | Placeholder key mismatch (`{{TITLE}}` ≠ `{{Title}}`); BODY markdown with unclosed fences renders oddly — keep it simple |
| Merge succeeds but PDF looks plain | Wrong path taken — you wanted the branded merge, or the template ODT was replaced by a bare one; re-check `list_templates` source |
| Batch pack missing files | Non-markdown inputs are skipped silently; check the `count` in the result vs your input list |
| `soffice` timeout on large packs | Raise `LIBREOFFICE_MCP_CONVERT_TIMEOUT_SEC`; split 50+ file packs into two runs |
| Downstream can't find the PDF | Output dir drift — confirm `GET /api/output` (respects `LIBREOFFICE_MCP_OUTPUT_DIR`); prefer explicit `output_stem` |

## Scheduling notes (fleet-agent)

- Weekly report: trigger Monday mornings; DATE = run date; archive prior PDFs (same
  stem overwrites silently when `output_stem` repeats).
- Board pack: KPI_TABLE is plain text — pre-format numbers upstream; the template
  does not compute.
- Artifact pack: point batch inputs at absolute paths (e.g. under
  `.fleet-agent/artifacts/`); the merge path needs FILE_COUNT set by hand.
- All three flows work headless — no GUI, no `:8765` bridge required.
