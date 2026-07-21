# Quality Check: libreoffice-mcp — 2026-07-22

**Elevator pitch:** Headless LibreOffice document automation for the fleet — convert, merge, batch pack, PDF ops, live Writer/Calc bridge via .oxt extension, UNO macros, agentic workflows.

**First commit:** 2026-04 (est. ~3 months old)

---

## Scorecard

| Dimension | Weight | Score | Weighted | Rationale |
|-----------|--------|-------|----------|-----------|
| **Originality** | 10% | 7 | 0.70 | 5+ LibreOffice MCP servers exist but all are basic CLI wrappers. This one has live Writer bridge, live Calc bridge, UNO macros, agentic sampling, Tauri desktop — first to go beyond `soffice --headless`. Novel for the category. |
| **Difficulty** | 10% | 7 | 0.70 | Medium-high. COM bridge via .oxt extension, subprocess orchestration, live SSE streaming, PyInstaller + Tauri packaging, FastMCP sampling handler. Not trivial but well within standard fleet patterns. |
| **Wrappee importance** | 15% | 8 | 1.20 | LibreOffice: 200M+ downloads, FOSS office standard, active development (26.x line), CLI + UNO COM API + extension system (.oxt). Stable LTS releases — maintenance burden is low. |
| **Competitive situation** | 10% | 7 | 0.70 | 5+ competitors but none match this feature set. WaterPistolAI (23⭐) is closest but CLI-only. jwingnut's `mcp-libre` (8⭐) is an in-app extension, not a headless server. This repo dominates on surface area. |
| **Tool surface** | 15% | 7 | 1.05 | 4 MCP tools (libreoffice portmanteau ~20 ops, libreoffice_writer, libreoffice_calc, libreoffice_help) + agentic workflow + 2 prefab cards + skills + prompts + resources. Good depth, portmanteau-patterned. |
| **Webapp quality** | 10% | 7 | 0.70 | After SOTA pass: hero section, data-testid, exponential backoff, Tauri listener, skill-first chat, personality injection, provider controls, GPU detection, streaming chat, color-scheme:dark. Still missing keyboard shortcuts, apps hub dynamic filtering, and dark native form controls. |
| **Fleet integration** | 15% | 7 | 1.05 | Consumed by fleet-agent-mcp (coworker PDF flows), email-mcp (PDF reports), immich-mcp (OCR pipeline), calibre-mcp (EPUB pipeline). Documented handoffs exist. No A2A configured yet. |
| **Battlegroup fit** | 15% | 8 | 1.20 | Productivity/Office battlegroup anchor. The premier FOSS office automation tool in the fleet — no other repo provides document generation, conversion, and live bridge for LibreOffice. |

| | |
|---|-----|
| **Total** | **7.3 / 10** |
| **Rating** | **Strong** — solid member, worth maintaining and investing in |

---

## Wrappability surface

| Surface | Used? | Detail |
|---------|-------|--------|
| CLI (`soffice --headless`) | ✅ Primary | Convert, merge, PDF export |
| COM / UNO API | ✅ Via .oxt extension | Live Writer typewriter, macros, Calc pivot |
| File format (ODT zip) | ✅ Direct | Template merge via zipfile manipulation |
| Plugin/extension (.oxt) | ✅ Shipped | Writer bridge, Calc bridge extensions |
| SDK (python-uno) | Available but not used | COM bridge is preferred for live interaction |

Release cadence: stable LTS — maintenance burden is low.

---

## Growth gaps

| Gap | Impact | Effort | Note |
|-----|--------|--------|------|
| **Repo is private** | **CRITICAL** | Low | Cannot be found, starred, or forked. Blocks all community growth. Make public. |
| **No CI/CD pipeline** | MEDIUM | Medium | No GitHub Actions. Tests don't run automatically. Manual testing only. |
| **No A2A integration** | MEDIUM | Medium | Could expose `/api/convert` and `/api/merge` as A2A capabilities for other agents. |
| **No README badges** | LOW | Low | Just, ruff, python, fastmcp version badges missing from top of README. First impression suffers. |
| **No env var table in README** | LOW | Low | Env vars documented in `docs/CONFIGURATION.md` but not surfaced in the main README. |
| **Tauri NSIS not release-certified** | LOW | Medium | `native/` exists but `just cua-nsis-test` hasn't been run and certified. |

---

## Competitor landscape

| Repo | Stars | Approach | Gap |
|------|-------|----------|-----|
| WaterPistolAI/libreoffice-mcp | 23 | CLI-only wrapper | No live bridge, no webapp, no Tauri |
| jwingnut/mcp-libre | 8 | In-app UNO extension | No headless mode, requires LibreOffice open |
| jwingnut/libreoffice-mcp-ubuntu | 3 | CLI-only, Ubuntu-focused | Linux-only, no Windows |
| sandraschi/libreoffice-mcp | 0 (private) | Full stack | Most comprehensive by far — invisible because private |
| passerbyflutter/libreoffice-mcp-tools | 0 | CLI read/write | Minimal, no live features |

**Verdict:** This repo dominates the LibreOffice MCP space in feature coverage but is invisible because it's private. Making it public would instantly make it the leading LibreOffice MCP server.

---

## Summary

**7.3/10 — Strong.** Solid technical foundation, comprehensive feature set, good fleet integration. The single highest-impact action is making the repo public. Everything else is polish.
