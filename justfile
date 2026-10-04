set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]
import 'scripts/just/fleet.just'

# Open interactive recipe dashboard (fleet standard)
default:
    @just --list

REPO := justfile_directory()

# --- Install ---

install:
    Set-Location "{{REPO}}"; uv sync --extra dev; powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap-webapp.ps1

sync:
    Set-Location "{{REPO}}"; uv sync --extra dev

bootstrap-web:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{{REPO}}/scripts/bootstrap-webapp.ps1"

# --- Runtime ---

backend:
    Set-Location "{{REPO}}"; uv run libreoffice-mcp --http --port 10981

mcp:
    Set-Location "{{REPO}}"; uv run libreoffice-mcp --stdio

# Full stack: backend :10981 + frontend :10983 (fleet launcher)
serve:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{{REPO}}/start.ps1"

webapp:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{{REPO}}/webapp/start.ps1"

start:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{{REPO}}/webapp/start.ps1"

# --- Quality ---

lint:
    Set-Location "{{REPO}}"; uv run ruff check src/ tests/; Set-Location "{{REPO}}/webapp"; npx @biomejs/biome ci src e2e

fix:
    Set-Location "{{REPO}}"; uv run ruff check src/ tests/ --fix; uv run ruff format src/ tests/; Set-Location "{{REPO}}/webapp"; npx @biomejs/biome check --write src e2e

# Format only (ruff format + biome write)
fmt:
    Set-Location "{{REPO}}"; uv run ruff format src/ tests/; Set-Location "{{REPO}}/webapp"; npx @biomejs/biome check --write src e2e

check:
    Set-Location "{{REPO}}"; uv run python -c "import libreoffice_mcp.server; print('Import OK')"

# All green: lint + tests (Python + webapp typecheck)
certify:
    Set-Location "{{REPO}}"; uv run ruff check src/ tests/; uv run ruff format src/ tests/ --check; uv run pytest tests/ -q; Set-Location "{{REPO}}/webapp"; npx tsc -b --noEmit; npx @biomejs/biome ci src e2e

# --- Testing ---

test:
    Set-Location "{{REPO}}"; uv run pytest tests/ -q

test-api:
    Set-Location "{{REPO}}"; uv run pytest tests/test_api.py -q

e2e:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{{REPO}}/scripts/bootstrap-webapp.ps1"; Set-Location "{{REPO}}/webapp"; npm run test:e2e

pack-oxt:
    powershell.exe -NoProfile -File "{{REPO}}/scripts/pack-bridge-oxt.ps1"

pack-calc-oxt:
    powershell.exe -NoProfile -File "{{REPO}}/scripts/pack-bridge-calc-oxt.ps1"

install-oxt:
    powershell.exe -NoProfile -File "{{REPO}}/scripts/install-bridge-oxt.ps1"

install-calc-oxt:
    powershell.exe -NoProfile -File "{{REPO}}/scripts/install-bridge-calc-oxt.ps1"

# Pack via the canonical pipeline (wipe + fresh-copy src -> mcpb/src, checks, pack).
# Never call bare `mcpb pack` — it ships a stale stage (see mcpb/pack.ps1).
pack mcpb-pack:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{{REPO}}/mcpb/pack.ps1"

# --- Native  Tauri 2 ---

build-webapp:
    Set-Location "{{REPO}}/webapp"; npm run build

build-native:
    $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"; & "{{REPO}}/native/build.ps1"

build-native-debug:
    Set-Location "{{REPO}}/native"; $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"; npx @tauri-apps/cli build --debug

tauri-sidecar:
    powershell.exe -NoProfile -File "{{REPO}}/native/build-sidecar.ps1"

tauri-build: build-native

tauri-dev:
    Set-Location "{{REPO}}/native"; $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"; npm install; npx @tauri-apps/cli dev

# Bootstrap: install dev deps + pre-commit hook
bootstrap:
    uv sync --group dev
    uv run pre-commit install
    Write-Host "Pre-commit hooks installed." -ForegroundColor Green
