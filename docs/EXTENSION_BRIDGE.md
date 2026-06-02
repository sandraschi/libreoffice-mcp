# LibreOffice MCP Bridge Extension (.oxt)

Shipped extension that auto-connects LibreOffice to libreoffice-mcp — live typing, UNO **Basic** and **Python** macros, no manual macro paste.

## Build

```powershell
Set-Location D:\Dev\repos\libreoffice-mcp
.\scripts\pack-bridge-oxt.ps1
```

Output: `dist/libreoffice-mcp-bridge.oxt`

## Install

### GUI

1. LibreOffice → **Tools → Extension Manager**
2. **Add** → select `dist/libreoffice-mcp-bridge.oxt`
3. Restart LibreOffice (or at least Writer)

### CLI (shared, all users)

```powershell
.\scripts\install-bridge-oxt.ps1
```

Or:

```powershell
& "C:\Program Files\LibreOffice\program\soffice.exe" --headless --invisible unopkg add --shared "D:\Dev\repos\libreoffice-mcp\dist\libreoffice-mcp-bridge.oxt"
```

## After install

- Bridge **auto-starts** on LibreOffice launch (`Jobs.xcu` → `onStartup`)
- **Tools → MCP Bridge** menu: Start / Stop / Status
- Polls `http://127.0.0.1:10981` (override with env `LIBREOFFICE_MCP_PORT`)

Start libreoffice-mcp first:

```powershell
just webapp
```

## UNO macro execution

Requires the extension running (heartbeat on :10981).

### Basic macro (application)

```python
libreoffice(
    operation='run_macro',
    macro_name='MyMacro',
    library='Standard',
    module='Module1',
    macro_location='application',
)
```

### Full script URI

```python
libreoffice(
    operation='run_macro',
    macro_uri='vnd.sun.star.script:Standard.Module1.Hello?language=Basic&location=application',
)
```

### Python macro

```python
libreoffice(operation='run_python_macro', macro_name='MyPythonMacro', library='Standard', module='Module1')
```

### List document macros

```python
libreoffice(operation='list_macros')
```

Open a document with embedded Basic modules first for document-scoped results.

## Legacy manual macro

`docs/writer_bridge_macro.py` remains for debugging without installing the .oxt. The extension supersedes it for normal use.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Bridge offline in webapp | LO running? Extension enabled? MCP on :10981? |
| Macro fails | Macro exists in Standard library; try `list_macros` with doc open |
| Port conflict | Set `LIBREOFFICE_MCP_PORT` before starting LO |
