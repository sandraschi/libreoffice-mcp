# LibreOffice host prerequisite

libreoffice-mcp is a **wrapper** around LibreOffice's `soffice` binary. It does not ship LibreOffice, Java, or UNO bindings. Every convert, merge, and export operation invokes:

```text
soffice --headless --convert-to <format> --outdir <dir> <file>
```

If LibreOffice is missing or not on PATH, nothing works.

---

## Install LibreOffice

### Windows

1. Download from [https://www.libreoffice.org/download/download/](https://www.libreoffice.org/download/download/)
2. Run the installer (64-bit recommended).
3. Default binary: `C:\Program Files\LibreOffice\program\soffice.exe`

```powershell
winget install TheDocumentFoundation.LibreOffice
```

Verify:

```powershell
& "C:\Program Files\LibreOffice\program\soffice.exe" --version
```

### macOS

1. Download the `.dmg` from libreoffice.org or `brew install --cask libreoffice`
2. Binary: `/Applications/LibreOffice.app/Contents/MacOS/soffice`

### Linux

```bash
# Debian/Ubuntu
sudo apt install libreoffice-writer libreoffice-calc libreoffice-impress

# Fedora
sudo dnf install libreoffice
```

Binary is usually `/usr/bin/soffice` or `/usr/bin/libreoffice`.

---

## Configure libreoffice-mcp

Auto-detection checks common paths (see `config.py`). Override when needed:

```env
LIBREOFFICE_MCP_SOFFICE_PATH=C:\Program Files\LibreOffice\program\soffice.exe
```

Restart the backend after changing `.env`.

---

## What LibreOffice provides

| App | Input examples | Typical exports |
|-----|----------------|-----------------|
| **Writer** | ODT, DOCX, RTF, MD*, PDF | PDF, DOCX, ODT, HTML |
| **Calc** | ODS, XLSX, CSV | PDF, XLSX, ODS, CSV |
| **Impress** | ODP, PPTX | PDF, PPTX, ODP |

\* Markdown is pre-rendered to HTML by libreoffice-mcp before convert.

---

## Extension bridge (optional)

For **live** document editing (cursor in Writer, macros, UNO tools), install a LibreOffice extension MCP:

- WriterAgent, mcp-libre, or similar
- Default bridge URL: `http://127.0.0.1:8765/mcp`

Headless convert does **not** require the extension.

---

## Version notes

Tested with LibreOffice **26.x** on Windows. Newer major versions may change filter names; report issues with `soffice --version` and the failing format.

---

## Not bundled in Tauri / MCPB

The Tauri installer (~15 MB) includes the Python MCP server and webapp. **LibreOffice remains a separate install** on every machine.
