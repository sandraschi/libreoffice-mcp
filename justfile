set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

# Open interactive recipe dashboard (fleet standard)
default:
    @pwsh.exe -NoProfile -ExecutionPolicy Bypass -File ../mcp-central-docs/scripts/just-dashboard.ps1 -Path .

REPO := justfile_directory()

# ── Install ───────────────────────────────────────────────────────────────────

install:
    Set-Location "{{REPO}}"
    uv sync --extra dev
    pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap-webapp.ps1

sync:
    Set-Location "{{REPO}}"
    uv sync --extra dev

bootstrap-web:
    pwsh -NoProfile -ExecutionPolicy Bypass -File "{{REPO}}/scripts/bootstrap-webapp.ps1"

# ── Runtime ───────────────────────────────────────────────────────────────────

backend:
    Set-Location "{{REPO}}"
    uv run libreoffice-mcp --http --port 10981

mcp:
    Set-Location "{{REPO}}"
    uv run libreoffice-mcp --stdio

webapp:
    pwsh -NoProfile -ExecutionPolicy Bypass -File "{{REPO}}/webapp/start.ps1"

start:
    pwsh -NoProfile -ExecutionPolicy Bypass -File "{{REPO}}/webapp/start.ps1"

# ── Quality ───────────────────────────────────────────────────────────────────

lint:
    Set-Location "{{REPO}}"
    uv run ruff check src/ tests/
    Set-Location "{{REPO}}/webapp"
    npx @biomejs/biome ci src e2e

fix:
    Set-Location "{{REPO}}"
    uv run ruff check src/ tests/ --fix
    uv run ruff format src/ tests/
    Set-Location "{{REPO}}/webapp"
    npx @biomejs/biome check --write src e2e

check:
    Set-Location "{{REPO}}"
    uv run python -c "import libreoffice_mcp.server; print('Import OK')"

# ── Testing ───────────────────────────────────────────────────────────────────

test:
    Set-Location "{{REPO}}"
    uv run pytest tests/ -q

test-api:
    Set-Location "{{REPO}}"
    uv run pytest tests/test_api.py -q

e2e:
    pwsh -NoProfile -ExecutionPolicy Bypass -File "{{REPO}}/scripts/bootstrap-webapp.ps1"
    Set-Location "{{REPO}}/webapp"
    npm run test:e2e

pack-oxt:
    pwsh -NoLogo -File "{{REPO}}/scripts/pack-bridge-oxt.ps1"

install-oxt:
    pwsh -NoLogo -File "{{REPO}}/scripts/install-bridge-oxt.ps1"

pack mcpb-pack:
    Set-Location "{{REPO}}"
    New-Item -ItemType Directory -Force -Path dist | Out-Null
    npx --yes @anthropic-ai/mcpb pack "{{REPO}}" "{{REPO}}/dist/libreoffice-mcp-v0.2.0.mcpb"
    Write-Host "Bundle: {{REPO}}/dist/libreoffice-mcp-v0.2.0.mcpb"

# ── Native (Tauri 2.0) ────────────────────────────────────────────────────────

build-webapp:
    Set-Location "{{REPO}}/webapp"
    npm run build

build-native:
    Set-Location "{{REPO}}/native"
    $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
    .\build.ps1

build-native-debug:
    Set-Location "{{REPO}}/native"
    $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
    npx @tauri-apps/cli build --debug

tauri-sidecar:
    pwsh -NoLogo -File "{{REPO}}/native/build-sidecar.ps1"

tauri-build: build-native

tauri-dev:
    Set-Location "{{REPO}}/native"
    $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
    npm install
    npx @tauri-apps/cli dev
