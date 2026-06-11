# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for libreoffice-mcp backend sidecar."""

from PyInstaller.utils.hooks import copy_metadata

datas = [("src/libreoffice_mcp", "libreoffice_mcp")]
for pkg in (
    "fastmcp",
    "fastapi",
    "uvicorn",
    "pydantic",
    "pydantic_settings",
    "starlette",
    "httpx",
    "prefab_ui",
):
    datas += copy_metadata(pkg)

a = Analysis(
    ["run_server.py"],
    pathex=["src"],
    binaries=[],
    datas=datas,
    hiddenimports=[
    "_strptime",
    "_datetime",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.asyncio",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.httptools_impl",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "prefab_ui.app",
        "prefab_ui.components",
        "libreoffice_mcp.sampling.lo_sampling_handler",
        "libreoffice_mcp.mcp_agentic",
        "pypdf",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "PIL", "pandas", "scipy"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="libreoffice-mcp-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
