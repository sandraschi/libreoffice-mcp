# Calc live bridge (.oxt)

Shipped extension: **`dist/libreoffice-mcp-calc-bridge.oxt`** — live cell typing and Data Pilot (pivot) in Calc GUI.

Patterns adapted from [jwingnut/mcp-libre](https://github.com/jwingnut/mcp-libre) (clone: `D:\Dev\repos\external\mcp-libre`). Headless spreadsheet read uses the same CSV-via-`soffice` approach as `read_spreadsheet_data` in upstream `libremcp.py`.

## Build and install

```powershell
Set-Location D:\Dev\repos\libreoffice-mcp
just pack-calc-oxt
just install-calc-oxt
```

Restart LibreOffice Calc (or full suite). Bridge auto-starts on LO launch.

## Backend

```powershell
just webapp
```

Polls `http://127.0.0.1:10981/api/v1/calc/*`.

## MCP portmanteau

```python
libreoffice_calc(operation="live_pivot_demo", typewriter_seed=True)
libreoffice_calc(operation="live_type_grid", cells=[{"row": 0, "col": 0, "value": "Hello"}])
libreoffice_calc(operation="set_cell", row=0, col=0, value="42")
libreoffice_calc(operation="create_pivot", source_range="A1:D7")
libreoffice_calc(operation="read_file", input_path="C:/data/sheet.xlsx")
```

## Webapp

**Live Calc** page (`/live-calc`) — pivot demo button + SSE event stream.

## Writer vs Calc extensions

| Extension | Menu | Endpoints |
|-----------|------|-----------|
| `libreoffice-mcp-bridge.oxt` | MCP Bridge | `/api/v1/writer/*` |
| `libreoffice-mcp-calc-bridge.oxt` | MCP Calc Bridge | `/api/v1/calc/*` |

Both can be installed together.

## Optional: mcp-libre on :8765

For full Writer UNO tools (track changes, comments), install upstream mcp-libre and use `libreoffice(operation="bridge_call", …)`.
