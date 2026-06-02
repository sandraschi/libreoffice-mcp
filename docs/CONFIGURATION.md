# Configuration

All settings use prefix `LIBREOFFICE_MCP_` (`.env` or environment). The Settings page writes to repo-root `.env` and hot-reloads.

## Core

| Variable | Default | Purpose |
|----------|---------|---------|
| `SOFFICE_PATH` | auto-detect | Path to `soffice.exe` / `soffice` — **required for convert/merge** |
| `EXTENSION_BRIDGE_URL` | `http://127.0.0.1:8765/mcp` | WriterAgent / mcp-libre MCP (optional live editing) |
| `HOST` | `127.0.0.1` | Backend bind |
| `PORT` | `10981` | Backend port |
| `CONVERT_TIMEOUT_SEC` | `120` | Headless job timeout |

## Directories

| Variable | Default | Purpose |
|----------|---------|---------|
| `TEMPLATES_DIR` | `~/.libreoffice-mcp/templates` | Custom ODT templates |
| `OUTPUT_DIR` | `~/.libreoffice-mcp/output` | Convert/merge output |
| `UPLOAD_DIR` | `~/.libreoffice-mcp/uploads` | Webapp upload staging |
| `DATA_DIR` | `~/.libreoffice-mcp/data` | SQLite jobs + output index |

## Watch & upload

| Variable | Default | Purpose |
|----------|---------|---------|
| `WATCH_POLL_SEC` | `5` | Folder watch polling interval |
| `MAX_UPLOAD_BYTES` | `52428800` (50 MB) | Max single upload size |

## Fleet & LLM

| Variable | Default | Purpose |
|----------|---------|---------|
| `CENTRAL_DOCS_PATH` | `D:\Dev\repos\mcp-central-docs` | Apps Hub registry |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Optional Ollama for sampling enrichment |
| `OLLAMA_MODEL` | `qwen3.5:27b` | Default chat/sampling model |
| `SAMPLING_BASE_URL` | `http://127.0.0.1:11434/v1` | Agentic workflow OpenAI-compatible API |
| `SAMPLING_MODEL` | `qwen3.5:27b` | Agentic sampling model |
| `LMSTUDIO_BASE_URL` | `http://127.0.0.1:1234` | Optional LM Studio |
| `OPENAI_API_KEY` | — | Optional cloud LLM |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model name |

See [.env.example](../.env.example) for a copy-paste template.
