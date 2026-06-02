# One-time / CI webapp dependency install (non-interactive, bounded)
$ErrorActionPreference = "Stop"
$Webapp = Join-Path $PSScriptRoot "..\webapp"
Set-Location $Webapp

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Error "npm not found on PATH"
}

Write-Host "=== libreoffice-mcp webapp bootstrap ===" -ForegroundColor Cyan

if (Test-Path "package-lock.json") {
    Write-Host "npm ci (from lockfile)..." -ForegroundColor Yellow
    npm ci --no-audit --no-fund --legacy-peer-deps
    if ($LASTEXITCODE -ne 0) {
        Write-Host "lockfile out of sync — npm install..." -ForegroundColor Yellow
        npm install --no-audit --no-fund --legacy-peer-deps
    }
} else {
    Write-Host "npm install (no lockfile yet)..." -ForegroundColor Yellow
    npm install --no-audit --no-fund --legacy-peer-deps
}

Write-Host "Playwright Chromium (e2e)..." -ForegroundColor Yellow
npx playwright install chromium

Write-Host "Done." -ForegroundColor Green
