# LibreOffice MCP Calc Bridge — UNO extension (.oxt)
# Polls libreoffice-mcp :10981 /api/v1/calc/* for live cell typing and pivot tables.

import json
import os
import threading
import time
import urllib.error
import urllib.request

import uno
import unohelper
from com.sun.star.sheet import DataPilotFieldOrientation
from com.sun.star.sheet import GeneralFunction
from com.sun.star.task import XJobExecutor

MCP_PORT = os.environ.get("LIBREOFFICE_MCP_PORT", "10981")
MCP_BASE = f"http://127.0.0.1:{MCP_PORT}"
POLL_SEC = 0.35

_bridge_thread = None
_bridge_stop = threading.Event()


def _get(path):
    req = urllib.request.Request(f"{MCP_BASE}{path}")
    with urllib.request.urlopen(req, timeout=3) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post(path, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{MCP_BASE}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _ctx_desktop(ctx):
    try:
        return XSCRIPTCONTEXT.getDesktop()  # noqa: F821
    except NameError:
        sm = ctx.ServiceManager
        return sm.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)


def _is_calc(doc):
    if doc is None:
        return False
    if doc.supportsService("com.sun.star.sheet.SpreadsheetDocument"):
        return True
    return hasattr(doc, "getSheets")


def _current_calc(desktop):
    doc = desktop.getCurrentComponent()
    if _is_calc(doc):
        return doc
    return None


def _sheet(doc, name=None):
    sheets = doc.getSheets()
    if name:
        return sheets.getByName(name)
    return sheets.getByIndex(0)


def _new_calc_doc(desktop):
    desktop.loadComponentFromURL("private:factory/scalc", "_blank", 0, ())
    return True


def _cell_value(cell, value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        cell.setValue(float(value))
    else:
        cell.setString(str(value))


def _set_cell(doc, action):
    sheet = _sheet(doc, action.get("sheet"))
    row = int(action.get("row", 0))
    col = int(action.get("col", 0))
    cell = sheet.getCellByPosition(col, row)
    _cell_value(cell, action.get("value", ""))
    return {"success": True, "row": row, "col": col}


def _set_range(doc, action):
    sheet = _sheet(doc, action.get("sheet"))
    start_row = int(action.get("start_row", 0))
    start_col = int(action.get("start_col", 0))
    values = action.get("values") or []
    for r_off, row_vals in enumerate(values):
        for c_off, val in enumerate(row_vals):
            cell = sheet.getCellByPosition(start_col + c_off, start_row + r_off)
            _cell_value(cell, val)
    return {"success": True, "rows": len(values)}


def _type_cells(doc, action):
    """Type into cells one-by-one so the user sees live updates in Calc."""
    sheet = _sheet(doc, action.get("sheet"))
    cells = action.get("cells") or []
    delay = float(action.get("delay_sec", 0.08))
    typed = 0
    for item in cells:
        row = int(item.get("row", 0))
        col = int(item.get("col", 0))
        cell = sheet.getCellByPosition(col, row)
        _cell_value(cell, item.get("value", ""))
        typed += 1
        if delay > 0:
            time.sleep(delay)
    return {"success": True, "typed_cells": typed}


def _get_range(doc, action):
    sheet = _sheet(doc, action.get("sheet"))
    r1 = int(action.get("start_row", 0))
    c1 = int(action.get("start_col", 0))
    r2 = int(action.get("end_row", r1))
    c2 = int(action.get("end_col", c1))
    data = []
    for r in range(r1, r2 + 1):
        row = []
        for c in range(c1, c2 + 1):
            cell = sheet.getCellByPosition(c, r)
            try:
                row.append(cell.getString())
            except Exception:
                row.append(str(cell.getValue()))
        data.append(row)
    return {"success": True, "data": data}


def _sheet_info(doc, action):
    sheet = _sheet(doc, action.get("sheet"))
    sheets = doc.getSheets()
    names = [sheets.getByIndex(i).getName() for i in range(sheets.getCount())]
    used = sheet.getUsedRange()
    addr = used.getRangeAddress()
    return {
        "success": True,
        "sheet": sheet.getName(),
        "sheet_names": names,
        "used": {
            "start_row": addr.StartRow,
            "start_col": addr.StartColumn,
            "end_row": addr.EndRow,
            "end_col": addr.EndColumn,
        },
    }


def _seed_demo_data(doc, action):
    """Sample sales grid for pivot demos (A1:D6)."""
    headers = [["Region", "Product", "Units", "Revenue"]]
    rows = [
        ["North", "Alpha", 12, 1200],
        ["North", "Beta", 8, 640],
        ["South", "Alpha", 20, 2000],
        ["South", "Gamma", 5, 750],
        ["East", "Beta", 15, 1350],
        ["West", "Gamma", 9, 1080],
    ]
    _set_range(doc, {"values": headers + rows, "start_row": 0, "start_col": 0})
    return {"success": True, "message": "demo_data_seeded", "rows": len(rows) + 1}


def _create_pivot(doc, action):
    sheet = _sheet(doc, action.get("sheet"))
    src = action.get("source_range") or "A1:D7"
    dest_row = int(action.get("dest_row", 8))
    dest_col = int(action.get("dest_col", 0))
    row_field = action.get("row_field") or "Region"
    data_field = action.get("data_field") or "Revenue"

    cell_range = sheet.getCellRangeByName(src)
    addr = cell_range.getRangeAddress()
    tables = sheet.getDataPilotTables()
    descriptor = tables.createDataPilotDescriptor()
    descriptor.setSourceRange(addr)

    fields = descriptor.getDataPilotFields()
    dim_row = fields.getDimension(int(DataPilotFieldOrientation.ROW))
    f_row = dim_row.append()
    f_row.setOrientation(DataPilotFieldOrientation.ROW)
    f_row.setName(row_field)
    f_row.setFunction(GeneralFunction.AUTO)

    dim_data = fields.getDimension(int(DataPilotFieldOrientation.DATA))
    f_data = dim_data.append()
    f_data.setOrientation(DataPilotFieldOrientation.DATA)
    f_data.setName(data_field)
    f_data.setFunction(GeneralFunction.SUM)

    name = action.get("pivot_name") or "FleetPivot"
    tables.insertNewByName(name, dest_row, dest_col, descriptor)
    return {
        "success": True,
        "pivot_name": name,
        "dest_row": dest_row,
        "dest_col": dest_col,
        "row_field": row_field,
        "data_field": data_field,
    }


def _macro_uri(macro_name, *, language="Basic", location="application", library=None, module=None):
    if macro_name.startswith("vnd.sun.star.script:"):
        return macro_name
    if library and module:
        path = f"{library}.{module}.{macro_name}"
    elif "." in macro_name:
        path = macro_name
    else:
        path = f"Standard.Module1.{macro_name}"
    return f"vnd.sun.star.script:{path}?language={language}&location={location}"


def _script_provider(ctx, desktop):
    doc = desktop.getCurrentComponent()
    if doc is not None:
        try:
            return doc.getScriptProvider()
        except Exception:
            pass
    sm = ctx.ServiceManager
    return sm.createInstanceWithContext("com.sun.star.script.Provider", ctx)


def _run_macro(ctx, desktop, action):
    uri = action.get("macro_uri")
    if not uri:
        uri = _macro_uri(
            action.get("macro_name") or "",
            language=action.get("language") or "Basic",
            location=action.get("location") or "application",
            library=action.get("library"),
            module=action.get("module"),
        )
    sp = _script_provider(ctx, desktop)
    script = sp.getScript(uri)
    args = action.get("args") or ()
    if not isinstance(args, tuple):
        args = tuple(args)
    result = script.invoke(args, (), ())
    return {"success": True, "output": str(result), "macro_uri": uri}


def _run_action(ctx, desktop, action):
    kind = action.get("action")
    doc = _current_calc(desktop)
    if kind == "new_document":
        _new_calc_doc(desktop)
        return {"success": True, "output": "new_calc_document"}
    if doc is None and kind not in ("new_document",):
        _new_calc_doc(desktop)
        doc = _current_calc(desktop)
    if doc is None:
        return {"success": False, "error": "No Calc document"}

    if kind == "set_cell":
        return _set_cell(doc, action)
    if kind == "set_range":
        return _set_range(doc, action)
    if kind == "type_cells":
        return _type_cells(doc, action)
    if kind == "get_range":
        return _get_range(doc, action)
    if kind == "sheet_info":
        return _sheet_info(doc, action)
    if kind == "seed_demo_data":
        return _seed_demo_data(doc, action)
    if kind == "create_pivot":
        try:
            return _create_pivot(doc, action)
        except Exception as exc:
            return {"success": False, "error": f"pivot failed: {exc}"}
    if kind in ("run_macro", "run_basic_macro"):
        return _run_macro(ctx, desktop, action)
    if kind == "run_python_macro":
        action = dict(action)
        action["language"] = "Python"
        return _run_macro(ctx, desktop, action)
    return {"success": False, "error": f"Unknown action: {kind}"}


def _poll_loop(ctx):
    desktop = _ctx_desktop(ctx)
    while not _bridge_stop.is_set():
        try:
            _post("/api/v1/calc/heartbeat", {})
            pending = _get("/api/v1/calc/pending")
            if pending.get("id"):
                try:
                    result = _run_action(ctx, desktop, pending.get("action") or {})
                    _post(
                        "/api/v1/calc/result",
                        {
                            "id": pending["id"],
                            "success": bool(result.get("success")),
                            "output": result.get("output", ""),
                            "error": result.get("error"),
                            "data": result,
                        },
                    )
                except Exception as exc:
                    _post(
                        "/api/v1/calc/result",
                        {"id": pending["id"], "success": False, "error": str(exc)},
                    )
        except urllib.error.URLError:
            pass
        except Exception:
            pass
        time.sleep(POLL_SEC)


def start_bridge(ctx):
    global _bridge_thread
    if _bridge_thread is not None and _bridge_thread.is_alive():
        return
    _bridge_stop.clear()
    _bridge_thread = threading.Thread(target=_poll_loop, args=(ctx,), daemon=True)
    _bridge_thread.start()


def stop_bridge():
    _bridge_stop.set()


class CalcStartupJob(unohelper.Base, XJobExecutor):
    def __init__(self, ctx):
        self.ctx = ctx

    def trigger(self, args):
        cmd = (args or "").strip()
        if cmd in ("", "onStartup", "StartCalcBridge"):
            start_bridge(self.ctx)
            return 0
        if cmd == "StopCalcBridge":
            stop_bridge()
            return 0
        if cmd == "CalcBridgeStatus":
            try:
                st = _get("/api/live/calc/status")
                msg = "connected" if st.get("calc_bridge_connected") else "offline"
            except Exception as exc:
                msg = str(exc)
            try:
                toolkit = self.ctx.ServiceManager.createInstanceWithContext(
                    "com.sun.star.awt.Toolkit", self.ctx
                )
                toolkit.createMessageBox(
                    None,
                    "infobox",
                    1,
                    "LibreOffice MCP Calc Bridge",
                    f"Bridge: {msg}\nServer: {MCP_BASE}",
                ).execute()
            except Exception:
                pass
            return 0
        start_bridge(self.ctx)
        return 0


g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationHelper.addImplementation(
    CalcStartupJob,
    "com.libreoffice.mcp.calc.bridge.StartupJob",
    ("com.sun.star.task.Job",),
)
