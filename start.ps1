Param(
    [switch]$Headless,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$NoBrowser,
    [switch]$Stdio,
    [int]$Port = 10981
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
if ($Stdio) {
    $ErrorActionPreference = "Stop"
    Set-Location $PSScriptRoot
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Error "uv not found on PATH"
    }
    uv sync
    uv run libreoffice-mcp --stdio
    exit $LASTEXITCODE
}

$FleetStartPath = Join-Path $ProjectRoot "scripts\FleetStartMode.ps1"
if (-not (Test-Path -LiteralPath $FleetStartPath)) {
    Write-Host "ERROR: Missing vendored launcher helper: $FleetStartPath" -ForegroundColor Red
    exit 1
}
. $FleetStartPath
Stop-FleetPortSquatters -Ports @(10981, 10983) -Label "libreoffice-mcp"

& (Join-Path $PSScriptRoot "webapp\start.ps1") @PSBoundParameters

