param(
    [switch]$Headless,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$NoBrowser
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$FleetStartPath = Join-Path $ProjectRoot "scripts\FleetStartMode.ps1"
if (-not (Test-Path -LiteralPath $FleetStartPath)) {
    Write-Host "ERROR: Missing vendored launcher helper: $FleetStartPath" -ForegroundColor Red
    exit 1
}
. $FleetStartPath
$FleetStart = Initialize-FleetStartMode @PSBoundParameters
Enter-FleetHeadlessConsole -Headless:$Headless -BackendOnly:$BackendOnly

$ErrorActionPreference = "Stop"
$WebPort = 10983
$BackendPort = 10981
$Soffice = "C:\Program Files\LibreOffice\program\soffice.exe"

Write-Host "=== libreoffice-mcp (FastMCP 3.2 + Vite dashboard) ===" -ForegroundColor Cyan

if (-not (Test-Path $Soffice)) {
    Write-Host "[warn] LibreOffice soffice not found at $Soffice" -ForegroundColor Yellow
    Write-Host "       Convert/merge jobs will fail until LO is installed or LIBREOFFICE_MCP_SOFFICE_PATH is set." -ForegroundColor Yellow
} else {
    $ver = (Get-Item $Soffice).VersionInfo.ProductVersion
    Write-Host "[host] LibreOffice $ver at $Soffice" -ForegroundColor Gray
}

Stop-FleetPortSquatters -Ports @($WebPort, $BackendPort)

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "uv not found on PATH"
}

Set-Location $PSScriptRoot
if ($FleetStart.RunFrontend -and -not (Test-Path "node_modules")) {
    Write-Host "Installing webapp dependencies..." -ForegroundColor Cyan
    if (Test-Path "package-lock.json") {
        npm ci --no-audit --no-fund --legacy-peer-deps
        if ($LASTEXITCODE -ne 0) {
            npm install --no-audit --no-fund --legacy-peer-deps
        }
    } else {
        npm install --no-audit --no-fund --legacy-peer-deps
    }
}

$backendProc = $null

if ($FleetStart.RunBackend) {
    Write-Host "Starting backend on port $BackendPort ..." -ForegroundColor Cyan
    uv sync --quiet --project $ProjectRoot | Out-Null

    $backendCmd = "Set-Location '$ProjectRoot'; uv run libreoffice-mcp --http --port $BackendPort"
    Start-Process powershell -ArgumentList "-NoProfile", "-WindowStyle", "Normal", "-Command", $backendCmd

    Write-Host "Waiting for backend /health on :$BackendPort ..." -ForegroundColor Cyan
    $ready = $false
    for ($i = 0; $i -lt 60; $i++) {
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:$BackendPort/health" `
                -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
            if ($r.StatusCode -eq 200) {
                $ready = $true
                break
            }
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    if (-not $ready) {
        Write-Host "Backend did not respond on /health within 60s. Check the backend window." -ForegroundColor Red
        exit 1
    }
    Write-Host "Backend ready at http://127.0.0.1:$BackendPort/mcp" -ForegroundColor Green
}

if (-not $FleetStart.RunFrontend) {
    while ($true) { Start-Sleep -Seconds 60 }
}

Write-Host "Starting Vite frontend on port $WebPort ..." -ForegroundColor Green

$frontendUrl = "http://127.0.0.1:$WebPort/"
if (-not $FleetStart.SkipBrowser) {
    $pollAndOpen = @"
for (`$i = 0; `$i -lt 60; `$i++) {
  try {
    `$null = Invoke-WebRequest -Uri '$frontendUrl' -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
    Start-Process '$frontendUrl'
    exit
  } catch {
    Start-Sleep -Seconds 1
  }
}
"@
    Start-Process powershell -ArgumentList "-NoProfile", "-WindowStyle", "Hidden", "-Command", $pollAndOpen
    Write-Host "Browser will open automatically when Vite is ready." -ForegroundColor Gray
}

Write-Host ""
Write-Host "  Dashboard : $frontendUrl" -ForegroundColor Cyan
Write-Host "  MCP HTTP  : http://127.0.0.1:$BackendPort/mcp" -ForegroundColor Cyan
Write-Host "  Health    : http://127.0.0.1:$BackendPort/health" -ForegroundColor Cyan
Write-Host ""

npm run dev -- --port $WebPort --host 127.0.0.1 --strictPort

