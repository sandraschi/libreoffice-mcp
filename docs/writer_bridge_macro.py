"""
writer_bridge_macro.py — LibreOffice Writer MCP Live Bridge

Run once with Writer open:
  Tools → Macros → Run Macro… → My Macros → writer_bridge_macro → Main

Keeps polling libreoffice-mcp for insert_text / new_document actions so you can
watch the agent type in the live Writer window.

Server: http://127.0.0.1:10981 (LIBREOFFICE_MCP_PORT)
"""

import json
import time
import urllib.error
import urllib.request

MCP_BASE = "http://127.0.0.1:10981"
POLL_SEC = 0.35


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
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _desktop():
    return XSCRIPTCONTEXT.getDesktop()  # noqa: F821 — provided by LO macro runtime


def _current_writer():
    doc = _desktop().getCurrentComponent()
    if doc is None:
        return None
    if not doc.supportsService("com.sun.star.text.GenericTextDocument"):
        return None
    return doc


def _new_writer_doc():
    _desktop().loadComponentFromURL("private:factory/swriter", "_blank", 0, ())
    return True


def _insert_text(text):
    doc = _current_writer()
    if doc is None:
        _new_writer_doc()
        doc = _current_writer()
    if doc is None:
        raise RuntimeError("Could not open Writer document")
    text_obj = doc.getText()
    cursor = text_obj.createTextCursor()
    cursor.gotoEnd(False)
    text_obj.insertString(cursor, text, False)
    return True


def _run_action(action):
    kind = action.get("action")
    if kind == "new_document":
        _new_writer_doc()
        return {"success": True, "output": "new_document"}
    if kind == "insert_text":
        _insert_text(action.get("text", ""))
        return {"success": True, "output": "insert_text"}
    return {"success": False, "error": f"Unknown action: {kind}"}


def Main(*args):
    """Poll libreoffice-mcp and execute Writer actions (blocking loop — keep macro running)."""
    try:
        _post("/api/v1/writer/heartbeat", {})
    except Exception:
        pass

    while True:
        try:
            _post("/api/v1/writer/heartbeat", {})
            pending = _get("/api/v1/writer/pending")
            if pending.get("id"):
                try:
                    result = _run_action(pending.get("action") or {})
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
        except urllib.error.URLError:
            pass
        except Exception:
            pass
        time.sleep(POLL_SEC)


def InsertTest(*args):
    """Quick test: insert one line without MCP server queue."""
    _insert_text("Hello from LibreOffice MCP bridge.\n")
    return None
