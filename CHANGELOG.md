
## [Unreleased] — 2026-10-04 (assfix)

### Added
- REST: `POST /api/shutdown` (orderly exit for service restarts), `GET /api/v1/diagnostics`
- REST: `/api/llm/providers`, `/api/llm/models`, `/api/llm/onboarding`,
  `/api/llm/chat` + `/api/llm/chat/stream` backend proxy aliases
- CI: `.github/workflows/ci.yml` (fleet template: ruff, pyright, pytest, tsc, biome, e2e)
- Session injection: `.cursorrules`, `.windsurfrules`, `.claude-plugin` + `hooks/`,
  `.github/copilot-instructions.md`, `.opencode/skills/`, `.agents/skills/`, `CLAUDE.md`
- Docs: `docs/ONBOARDING.md`; `llms-full.txt` route list synced
- Tool surface: `annotations=` on all portmanteaus, `## Return Format` + `## Examples`
- Tests: 6 new API tests (shutdown dry-run, diagnostics, llm aliases); coverage floor 45%

### Fixed
- CORS `allow_origin_regex` unconditional (was gated on `LIBREOFFICE_TAURI`)
- Ruff: removed `S110`/`S112` footgun ignores, enabled `T20` print ban
- Pyright: 16 pre-existing errors fixed (PrefabApp/Card kwargs were runtime bugs too)
- Webapp: `@tauri-apps/api` dep, dead `@ts-expect-error`s, biome.json v2 schema,
  unused imports/vars, CRLF normalization (`.gitattributes`)
- `justfile`: joined split `Set-Location` recipes; `pack` delegates to `mcpb/pack.ps1`
- `.gitignore`: fixed `reports/` typo, added `*.mcpb`/`*.bak*`, `uv.lock` now committed

## [Unreleased] — 2026-06-14

### Fixed
- Tauri build: resolved Rust crate conflict (brotli/alloc-no-stdlib)
- Tauri build: fixed PyInstaller path mismatch (hyphen to underscore in src dirs)
- Tauri build: fixed TypeScript errors (unused imports, useRef arg, import.meta.env)
- Tauri CORS: allow_origins includes tauri://localhost for WebView access

### Added
- CUA-NSIS: just cua-nsis-test recipe, smoke script, config
- CUA-NSIS: build.ps1 now copies NSIS installer to dist/
- CUA-NSIS: 11-phase smoke test (install, launch, WebView OCR, diagnostics, uninstall)
- CUA-NSIS: local certification — all 11 phases pass locally (2026-06-14)

# Changelog

## 0.3.0 (2026-06-01) — Shipped .oxt bridge + UNO macros

### Added

- **`dist/libreoffice-mcp-bridge.oxt`** — installable extension (auto-start on LO launch)
- **UNO macro ops** — `run_macro`, `run_python_macro`, `list_macros` via live bridge
- `scripts/pack-bridge-oxt.ps1`, `scripts/install-bridge-oxt.ps1`
- [docs/EXTENSION_BRIDGE.md](docs/EXTENSION_BRIDGE.md)

### Changed

- Live Write workflow prefers .oxt over manual `writer_bridge_macro.py`
- Version 0.3.0

## 0.2.0 (2026-05-30) — General-purpose LibreOffice automation

### Added

- **15 portmanteau operations** — `convert_batch`, `document_info`, `pdf_merge`, `watch_start/stop/status`, `reveal_output`
- **Formats module** — Writer/Calc/Impress detection and suggested export formats
- **Rich ODF merge** — markdown in BODY/NARRATIVE placeholders → styled ODF
- **SQLite persistence** — jobs + output index under `~/.libreoffice-mcp/data/`
- **Folder watch** — auto-convert incoming files
- **Upload API + webapp page** — drag-drop when paths are awkward
- **Agentic Chat** — `POST /api/chat` planner + execute
- **Tests page** — live self-tests including optional `soffice` convert
- **Tauri native** — desktop wrapper (bundles Python, not LibreOffice)
- **Multifile docs** — `INSTALL.md` (LibreOffice prerequisite first), `docs/LIBREOFFICE.md`, `docs/FEATURES.md`

### Changed

- README repositioned as general LibreOffice tool (not Fritz/PDF-only)
- MCPB pack artifact `libreoffice-mcp-v0.2.0.mcpb`

## Unreleased

Initial release: headless LibreOffice automation for Fritz coworker PDF/ODT deliverables.

### Added

- **Portmanteau MCP tool `libreoffice`** — `status`, `convert`, `merge`, `list_templates`, `batch_pack`, `bridge_discover`, `bridge_call`, `help`
- **Headless convert** — `soffice --headless`; `.md` → HTML → PDF
- **ODT template merge** — `{{PLACEHOLDER}}` substitution; bundled templates v2 (Writer styles: DocTitle, DocMeta, SectionHeading, BodyText, A4 margins)
- **Bundled templates** — `fleet-report.odt`, `fleet-board-pack.odt`, `fleet-artifact-pack.odt` (auto-seeded in `~/.libreoffice-mcp/templates/`, version file `.builtin-version`)
- **Extension bridge** — proxy to WriterAgent / mcp-libre on `:8765/mcp`
- **REST API** — `/api/templates`, `/api/merge`, `/api/pack`, `/api/convert`, `/api/jobs`, `/api/output`, `/api/output/file/{name}`
- **Webapp** — Vite dashboard on **10983** (template gallery, job queue, PDF preview)
- **fleet_bridge** alias `libreoffice` → `:10981/mcp`

### Fritz integration

| Coworker flow | libreoffice use |
|---------------|-----------------|
| `coworker_weekly_report_pdf` | `fleet-report.odt` merge → PDF |
| `coworker_board_pack` | `fleet-board-pack.odt` merge → PDF |
| `coworker_artifact_pack` | `fleet-artifact-pack.odt` merge → PDF |

### Registry

- [WEBAPP_PORTS.md](../mcp-central-docs/operations/WEBAPP_PORTS.md) — 10981 backend, 10983 frontend
- [webapp-registry.json](../mcp-central-docs/operations/webapp-registry.json) — `libreoffice-mcp-backend`, `libreoffice-mcp-frontend`

### Tests

- 17 pytest tests (`tests/` incl. `test_api.py` REST coverage)
- 9 Playwright e2e tests (`webapp/e2e/`) — dashboard navigation, templates, tools hub, REST
