# Installation

Install **LibreOffice on the host first**. libreoffice-mcp does not bundle LibreOffice — it shells out to `soffice`. Without it, convert/merge operations fail.

---

## Step 1 — Install LibreOffice (required)

See **[docs/LIBREOFFICE.md](docs/LIBREOFFICE.md)** for platform-specific instructions.

| Platform | Typical `soffice` path |
|----------|------------------------|
| Windows | `C:\Program Files\LibreOffice\program\soffice.exe` |
| macOS | `/Applications/LibreOffice.app/Contents/MacOS/soffice` |
| Linux | `/usr/bin/soffice` or `/usr/bin/libreoffice` |

**Verify after install:**

```powershell
# Windows
& "C:\Program Files\LibreOffice\program\soffice.exe" --version

# Or via MCP after setup
uv run libreoffice-mcp --http --port 10981
# GET http://127.0.0.1:10981/health  → soffice_available: true
```

If auto-detection fails, set in `.env`:

```env
LIBREOFFICE_MCP_SOFFICE_PATH=C:\Program Files\LibreOffice\program\soffice.exe
```

---

## Step 2 — Install libreoffice-mcp

### Option A — Claude Desktop (.mcpb)

1. Download `libreoffice-mcp-v0.2.0.mcpb` from GitHub Releases (or `just mcpb-pack` locally).
2. Drag the `.mcpb` onto Claude Desktop.
3. Configure **soffice path** when prompted if LibreOffice is non-standard.
4. Requires **Python 3.12+** on the host.

### Option B — mcpb CLI

```powershell
npx @anthropic-ai/mcpb install https://github.com/sandraschi/libreoffice-mcp
```

### Option C — Full stack (recommended)

```powershell
winget install Casey.Just   # optional recipe runner
git clone https://github.com/sandraschi/libreoffice-mcp
cd libreoffice-mcp
just install
just webapp
```

Opens **http://127.0.0.1:10983** (backend **10981**).

MCD launcher: `mcp-central-docs\starts\libreoffice-mcp-start.bat`

### Option D — Native desktop (Tauri)

Bundles the Python backend + webapp UI. **Still requires LibreOffice on the machine.**

```powershell
Set-Location native
.\build.ps1
```

Installer: `native\target\release\bundle\nsis\LibreOffice MCP_0.3.0-alpha.1_x64-setup.exe` (or download from [GitHub Releases](https://github.com/sandraschi/libreoffice-mcp/releases))

### Option E — Live Writer bridge extension (.oxt)

Enables **watch-it-write** and **UNO macro** execution in the live Writer window.

```powershell
.\scripts\pack-bridge-oxt.ps1
.\scripts\install-bridge-oxt.ps1
```

Restart LibreOffice after install. See [docs/EXTENSION_BRIDGE.md](docs/EXTENSION_BRIDGE.md).

---

## Prerequisites summary

| Component | Required | Notes |
|-----------|----------|-------|
| **LibreOffice** | **Yes** | Writer, Calc, Impress — [docs/LIBREOFFICE.md](docs/LIBREOFFICE.md) |
| Python 3.12+ | Yes | via [uv](https://docs.astral.sh/uv/) |
| Node.js 20+ | Webapp only | Vite dashboard |
| Rust + WebView2 | Tauri only | Windows native build |

Optional:

- **Extension MCP** (WriterAgent / mcp-libre) on `:8765` for live GUI editing
- **Ollama** for agentic plan enrichment (Chat uses built-in planner by default)

---

## Stdio (Cursor / Claude Desktop dev)

```powershell
uv sync --extra dev
copy .env.example .env
uv run libreoffice-mcp --stdio
```

MCP config example:

```json
{
  "mcpServers": {
    "libreoffice-mcp": {
      "command": "uv",
      "args": ["--directory", "D:\\Dev\\repos\\libreoffice-mcp", "run", "libreoffice-mcp", "--stdio"]
    }
  }
}
```

---

## Verify installation

```powershell
just check
just test
curl http://127.0.0.1:10981/health
```

Webapp **Tests** page runs live self-tests including optional `soffice` convert.

---

## Troubleshooting

- `soffice_available: false` → [docs/LIBREOFFICE.md](docs/LIBREOFFICE.md) + [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- Conversion errors → check stderr in job result; increase `LIBREOFFICE_MCP_CONVERT_TIMEOUT_SEC`
