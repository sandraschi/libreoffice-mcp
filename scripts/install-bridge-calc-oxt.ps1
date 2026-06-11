#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Oxt = Join-Path $Root "dist\libreoffice-mcp-calc-bridge.oxt"
if (-not (Test-Path $Oxt)) {
    & "$PSScriptRoot\pack-bridge-calc-oxt.ps1"
}
$soffice = $env:LIBREOFFICE_MCP_SOFFICE_PATH
if (-not $soffice) {
    $soffice = "C:\Program Files\LibreOffice\program\soffice.exe"
}
if (-not (Test-Path $soffice)) {
    throw "soffice not found at $soffice"
}
& $soffice --headless --invisible unopkg add --shared $Oxt
Write-Host "Installed shared: $Oxt" -ForegroundColor Green
