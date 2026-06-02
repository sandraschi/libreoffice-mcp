Param(
    [switch]$Headless,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$NoBrowser,
    [switch]$Stdio,
    [int]$Port = 10981
)

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

& (Join-Path $PSScriptRoot "webapp\start.ps1") @PSBoundParameters
