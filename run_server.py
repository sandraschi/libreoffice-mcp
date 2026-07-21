"""Entry point for PyInstaller-bundled libreoffice-mcp backend sidecar."""
import _strptime  # noqa: F401
import sys

sys.path.insert(0, ".")

from libreoffice_mcp.server import main

main()

