# Onboarding — libreoffice-mcp

Get productive in ~10 minutes: install the wrappee, verify the server, connect
an LLM (optional — convert/merge work without one).

## What for

- Headless document convert (Writer/Calc/Impress → PDF/DOCX/ODT/XLSX/HTML/CSV)
- ODT template merge (`{{PLACEHOLDERS}}` → styled PDF packs for coworker flows)
- Optional live Writer/Calc typewriter + UNO macros via the `.oxt` bridges

## Money / accounts

- **LibreOffice: free.** Download 26.x from libreoffice.org. No key, no account.
- **Local LLM (recommended, free):** Ollama + `qwen3.5:27b` for agentic workflows
  and Chat. No account.
- **Cloud LLM (optional, paid):** `LIBREOFFICE_MCP_OPENAI_API_KEY` enables the
  OpenAI fallback in Chat. Only set this if you want cloud completions.

## Pitfalls

1. **soffice not found** — set `LIBREOFFICE_MCP_SOFFICE_PATH` to your
   `soffice.exe` (e.g. `C:\Program Files\LibreOffice\program\soffice.exe`).
   Copy `.env.example` to `.env` first; never commit `.env`.
2. **Headless is the default.** Most tools spawn headless `soffice` themselves.
   Open Writer + run the bridge macro ONLY for live typewriter sessions
   (see `docs/LIVE_WRITER.md`).
3. **Extension bridge (:8765) is optional.** `bridge_discover`/`bridge_call`
   need WriterAgent or mcp-libre running there; everything else works without it.
4. **Sampling needs an LLM.** `libreoffice_agentic_workflow` uses
   `LIBREOFFICE_MCP_SAMPLING_BASE_URL` (default Ollama `http://127.0.0.1:11434/v1`).
   Without any LLM, Chat falls back to the rule-based planner (still useful).

## Sanity check

```powershell
just install
just serve   # backend :10981 + frontend :10983
```

1. Open **http://127.0.0.1:10983** — Dashboard shows green backend dot.
2. Run `libreoffice(operation="status")` — `soffice_available: true`.
3. Convert one file: `libreoffice(operation="convert", input_path="<a .md file>",
   output_format="pdf")` — find the PDF via `GET /api/output`.
4. Optional: set `LIBREOFFICE_MCP_SAMPLING_MODEL`, restart backend, try Chat.

When all four pass, onboarding is complete — the **MOCK** sample state (if any)
clears and live data takes over.
