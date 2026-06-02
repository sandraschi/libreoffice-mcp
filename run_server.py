"""Entry point for PyInstaller-bundled libreoffice-mcp backend sidecar."""
import sys

sys.path.insert(0, ".")

from libreoffice_mcp.server import main

main()
