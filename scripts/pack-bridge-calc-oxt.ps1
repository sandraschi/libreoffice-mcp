#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Src = Join-Path $Root "extension\libreoffice-mcp-calc-bridge"
$Dist = Join-Path $Root "dist"
$Zip = Join-Path $Dist "libreoffice-mcp-calc-bridge.zip"
$Oxt = Join-Path $Dist "libreoffice-mcp-calc-bridge.oxt"

if (-not (Test-Path $Src)) {
    throw "Extension source not found: $Src"
}

New-Item -ItemType Directory -Force -Path $Dist | Out-Null
if (Test-Path $Zip) { Remove-Item -LiteralPath $Zip -Force }
if (Test-Path $Oxt) { Remove-Item -LiteralPath $Oxt -Force }

Push-Location $Src
try {
    Compress-Archive -Path * -DestinationPath $Zip -CompressionLevel Optimal
} finally {
    Pop-Location
}

Rename-Item -LiteralPath $Zip -NewName (Split-Path $Oxt -Leaf)
Write-Host "Built: $Oxt" -ForegroundColor Green
Write-Host "Install: Tools -> Extension Manager -> Add -> $Oxt"
