# Live Studio Plan

Unified hub for live LibreOffice sessions (Writer, Calc, Impress) in the libreoffice-mcp webapp.

**Route:** `/studio` · **API:** `/api/studio/*`

## Vision

Live Studio is the front door for *hands-in / hands-out* workflows: see bridge health, jump to Live Write or Live Calc, launch LibreOffice GUI apps, and open recent output files in the right LO family after jobs complete.

Headless convert/merge remains on Dashboard, Convert, and Workflows. Live Studio focuses on **live GUI + bridge status**.

---

## Phase A (now)

**Goal:** Hub page + session API + open-in-app.

| Deliverable | Detail |
|-------------|--------|
| `/studio` page | Session bar (soffice, writer bridge, calc bridge), cards to `/live-write` and `/live-calc` |
| `GET /api/studio/session` | `build_studio_session()` — availability, bridge flags, output dir, live page links, recent outputs |
| `POST /api/studio/open-in-app` | `{ family, path? }` → launch Writer/Calc/Impress GUI; optional file from output dir (path validated) |
| `lo_gui.py` | `launch_lo_gui(family, document_path)` — shared Popen pattern |
| Post-job hook (manual) | User opens output from Studio list after convert/merge jobs |

**Out of scope for A:** Impress live bridge, cross-page persistent bar, fleet email hooks.

---

## Phase B — Impress headless + GUI

- [x] Launch Impress GUI from Studio (Phase A button)
- [x] Outline → slides: markdown `#` / `##` / `-` → `.odp` (`impress_outline.py`)
- [x] `POST /api/studio/outline-to-slides` + Studio UI panel
- [x] "Build and open Impress" after outline jobs
- [ ] Richer slide layouts / master templates (optional)

---

## Phase C — Session persistence

- [x] `StudioSessionBar` shared on Studio, Live Write, Live Calc, Output
- [x] "Open in LO" on Output (family from extension)
- [x] `localStorage` last-launched family (`studioFamily.ts`)
- [ ] Full-width session bar on Chat (optional)

---

## Phase D — Impress live bridge (if needed)

- Evaluate whether Impress needs a dedicated `.oxt` bridge (like Writer/Calc)
- Only build if Phase B GUI-open is insufficient for slide-by-slide live edits
- Reuse calc/writer poll/result HTTP pattern if proceeding

---

## Phase E — Fleet coworker hooks

- Email PDF attach (email-mcp integration after job complete)
- Fritz / fleet-agent notification on board-pack ready
- Optional: open generated PDF in system viewer + LO source doc side-by-side

---

## Related docs

- [LIVE_WRITER.md](LIVE_WRITER.md)
- [EXTENSION_CALC_BRIDGE.md](EXTENSION_CALC_BRIDGE.md)
- [FEATURES.md](FEATURES.md)

## Ports

| Service | Port |
|---------|------|
| Backend | 10981 |
| Webapp | 10983 |
| Extension bridge | 8765 |
