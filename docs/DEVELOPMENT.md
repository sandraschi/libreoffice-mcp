# Development

## Setup

```powershell
just install
```

## Commands

| Recipe | Action |
|--------|--------|
| `just` | Recipe dashboard |
| `just webapp` | Full stack |
| `just backend` | API only :10981 |
| `just mcp` | Stdio MCP |
| `just lint` | Ruff + Biome |
| `just fix` | Auto-fix |
| `just test` | pytest |
| `just e2e` | Playwright |

## Layout

```
src/libreoffice_mcp/   Python MCP + FastAPI (formats, storage, watch, pdf_ops, …)
webapp/                Vite React SOTA dashboard (Upload, Tests, agentic Chat)
tests/                 pytest (TestClient + optional live soffice)
docs/                  User/dev docs (INSTALL.md at repo root)
native/                Tauri 2 desktop wrapper (bundles Python, not LibreOffice)
```

## Code quality

- Python: **ruff** (`pyproject.toml`)
- Webapp: **Biome** (`webapp/biome.json`)

## Adding templates

Place `.odt` files in `templates_dir` or extend `ensure_builtin_templates()` in `templates.py`.
