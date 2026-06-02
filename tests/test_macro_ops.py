"""Macro URI builder tests."""

from __future__ import annotations

import pytest

from libreoffice_mcp.macro_ops import build_macro_uri, list_macros_action, macro_action_payload


def test_build_macro_uri_standard():
    uri = build_macro_uri("Hello", library="Standard", module="Module1")
    assert uri.startswith("vnd.sun.star.script:")
    assert "Standard.Module1.Hello" in uri
    assert "language=Basic" in uri


def test_build_macro_uri_passthrough():
    raw = "vnd.sun.star.script:Foo.Bar?language=Python&location=document"
    assert build_macro_uri(raw) == raw


def test_macro_action_payload():
    action = macro_action_payload(macro_name="Test", language="Python", location="document")
    assert action["action"] == "run_python_macro"
    assert action["macro_name"] == "Test"


def test_macro_action_requires_name():
    with pytest.raises(ValueError):
        macro_action_payload()


def test_list_macros_action():
    assert list_macros_action()["action"] == "list_macros"
