# LibreOffice MCP Live Bridge — UNO extension (install as .oxt)
# Polls libreoffice-mcp :10981 and executes Writer actions + Basic/Python macros.

import json
import os
import threading
import time
import urllib.error
import urllib.request

import uno
import unohelper
from com.sun.star.task import XJobExecutor

MCP_PORT = os.environ.get("LIBREOFFICE_MCP_PORT", "10981")
MCP_BASE = f"http://127.0.0.1:{MCP_PORT}"
POLL_SEC = 0.35

_bridge_thread = None
_bridge_stop = threading.Event()
_pending_lock = threading.Lock()
_pending_job = None


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
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _ctx_desktop(ctx):
    try:
        return XSCRIPTCONTEXT.getDesktop()  # noqa: F821
    except NameError:
        sm = ctx.ServiceManager
        return sm.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)


def _current_writer(desktop):
    doc = desktop.getCurrentComponent()
    if doc is None:
        return None
    if not doc.supportsService("com.sun.star.text.GenericTextDocument"):
        return None
    return doc


def _new_writer_doc(desktop):
    desktop.loadComponentFromURL("private:factory/swriter", "_blank", 0, ())
    return True


def _insert_text(desktop, text):
    doc = _current_writer(desktop)
    if doc is None:
        _new_writer_doc(desktop)
        doc = _current_writer(desktop)
    if doc is None:
        raise RuntimeError("Could not open Writer document")
    text_obj = doc.getText()
    cursor = text_obj.createTextCursor()
    cursor.gotoEnd(False)
    text_obj.insertString(cursor, text, False)
    return True


def _macro_uri(
    macro_name,
    *,
    language="Basic",
    location="application",
    library=None,
    module=None,
):
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


def _list_macros(desktop):
    found = []
    doc = desktop.getCurrentComponent()
    if doc is not None and hasattr(doc, "BasicLibraries"):
        libs = doc.BasicLibraries
        for lib_name in libs.getLibraryNames():
            lib = libs.getByName(lib_name)
            for mod_name in lib.getElementNames():
                found.append(
                    {
                        "library": lib_name,
                        "module": mod_name,
                        "location": "document",
                        "language": "Basic",
                    }
                )
    return {
        "success": True,
        "macros": found,
        "hint": "Application macros: use library.module.macro with location=application",
    }


def _run_action(ctx, desktop, action):
    kind = action.get("action")
    if kind == "new_document":
        _new_writer_doc(desktop)
        return {"success": True, "output": "new_document"}
    if kind == "insert_text":
        _insert_text(desktop, action.get("text", ""))
        return {"success": True, "output": "insert_text"}
    if kind in ("run_macro", "run_basic_macro"):
        return _run_macro(ctx, desktop, action)
    if kind == "run_python_macro":
        action = dict(action)
        action["language"] = "Python"
        return _run_macro(ctx, desktop, action)
    if kind == "list_macros":
        return _list_macros(desktop)
    return {"success": False, "error": f"Unknown action: {kind}"}


def _poll_loop(ctx):
    global _pending_job
    desktop = _ctx_desktop(ctx)
    while not _bridge_stop.is_set():
        try:
            _post("/api/v1/writer/heartbeat", {})
            pending = _get("/api/v1/writer/pending")
            if pending.get("id"):
                with _pending_lock:
                    _pending_job = pending
                try:
                    result = _run_action(ctx, desktop, pending.get("action") or {})
                    _post(
                        "/api/v1/writer/result",
                        {
                            "id": pending["id"],
                            "success": bool(result.get("success")),
                            "output": result.get("output", ""),
                            "error": result.get("error"),
                        },
                    )
                except Exception as exc:
                    _post(
                        "/api/v1/writer/result",
                        {"id": pending["id"], "success": False, "error": str(exc)},
                    )
                finally:
                    with _pending_lock:
                        _pending_job = None
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


class StartupJob(unohelper.Base, XJobExecutor):
    """Job executor — auto-start bridge + Tools menu commands."""

    def __init__(self, ctx):
        self.ctx = ctx

    def trigger(self, args):
        cmd = (args or "").strip()
        if cmd in ("", "onStartup", "StartBridge"):
            start_bridge(self.ctx)
            return 0
        if cmd == "StopBridge":
            stop_bridge()
            return 0
        if cmd == "BridgeStatus":
            try:
                st = _get("/api/live/status")
                msg = "connected" if st.get("writer_bridge_connected") else "offline"
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
                    "LibreOffice MCP Bridge",
                    f"Bridge: {msg}\nServer: {MCP_BASE}",
                ).execute()
            except Exception:
                pass
            return 0
        start_bridge(self.ctx)
        return 0


g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationHelper.addImplementation(
    StartupJob,
    "com.libreoffice.mcp.bridge.StartupJob",
    ("com.sun.star.task.Job",),
)
