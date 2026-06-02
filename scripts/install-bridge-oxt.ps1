#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Oxt = Join-Path $Root "dist\libreoffice-mcp-bridge.oxt"

if (-not (Test-Path $Oxt)) {
    & (Join-Path $Root "scripts\pack-bridge-oxt.ps1")
}

$candidates = @(
    "C:\Program Files\LibreOffice\program\soffice.exe",
    "C:\Program Files (x86)\LibreOffice\program\soffice.exe"
)
$soffice = $null
foreach ($c in $candidates) {
    if (Test-Path $c) { $soffice = $c; break }
}
if (-not $soffice) {
    throw "soffice.exe not found. Install LibreOffice first."
}

& $soffice --headless --invisible unopkg add --shared $Oxt
Write-Host "Extension installed (shared). Restart LibreOffice Writer." -ForegroundColor Green
