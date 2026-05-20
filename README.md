# compass

> An AI coach that helps me understand my world better and not miss things — pull-default, glance-paced, with persistent layered memory.

`compass` is a wearable AI coach. Three modes share one backend:

- **Visual** — tap → camera capture → "what is this?" / "does this match the drawing?" → directive on HUD.
- **Verbal** — voice trigger → ask anything → directive on HUD.
- **Retro** — button-press → process the last N minutes of conversation buffer → "what did they just ask?" / "summarize the last 10 min" / "what did we decide?"

All three feed and draw from a **layered, lossy memory pipeline** — rolling audio buffer → session transcript → session summary → daily digest → project memory — so compass can answer at any zoom level from "five minutes ago" to "what's the through-line of the Zahner project."

The hardware is abstracted. Today the visual mode runs against a mock (laptop webcam + simulated HUD window) so the whole pipeline is built and iterated before any glasses arrive. When real hardware ships, only the driver in `src/compass/glasses/` changes.

This project is the glance-paced sibling of [scan-to-action](https://github.com/barnes-ngb/) — same instrument pattern (*capture → reconcile → directive → log*), different rhythm of human attention. See `docs/portfolio-fit.md`.

---

## Thesis

> *"Understand my world better, don't miss things, get insight from the wealth of knowledge plus me."*

Pull-default — compass speaks when invoked, not when it feels like it. Persistent memory — it knows my projects, my goals, my patterns over time. Layered — it can answer about five minutes ago or five months ago using the same prompt surface. Honest about its boundaries — processes my own working memory of conversations I'm in, never records continuously, never surveils others.

---

## Status

- ✅ Phase 0: project scaffold, mock visual pipeline, three-mode architecture
- ⏳ Phase 1: real hardware integration (see `docs/landscape.md`)
- ⏳ Phase 2: verbal + retro modes wired to real STT and layered memory
- ⏳ Phase 3: domain-specific coach personas (fabrication, knowledge, life)

---

## Docs

| File | What's in it |
|---|---|
| `docs/architecture.md` | Module responsibilities, the three modes, sequence diagrams, latency budgets |
| `docs/roadmap.md` | Phases 0 → 3, exit criteria, backlog |
| `docs/landscape.md` | Smart-glasses landscape + scheduled re-check triggers |
| `docs/portfolio-fit.md` | How compass sits alongside scan-to-action, patina-model, directive-engine |
| `docs/decisions/0001-mock-first.md` | Build against a mock before buying hardware |
| `docs/decisions/0002-glasses-abstraction.md` | Why `Glasses` is a Protocol, not an ABC |
| `docs/decisions/0003-vlm-provider.md` | Why Claude Sonnet 4.6 is the default |
| `docs/decisions/0004-hardware-strategy.md` | Why we're not buying Frame new; the V0 / Z100 / M400 / Mentra Live decision tree |
| `docs/decisions/0005-coach-modes.md` | The three modes (Visual / Verbal / Retro) and their shared backend |
| `docs/decisions/0006-memory-layers.md` | Layered lossy memory pipeline + tap-to-tap V0 session model |
| `docs/decisions/0007-thesis-and-name.md` | Why "compass," and the thesis sentence |
| `web/compass.md` | Draft Astro page for the portfolio site |

---

## Requirements

- Windows 10/11 (PowerShell 5.1+ or 7)
- Python 3.11 or 3.12
- A webcam (built-in is fine)
- An Anthropic API key — https://console.anthropic.com/

No admin rights. No Docker. No global installs.

---

## Setup (PowerShell)

```powershell
# 1. Clone (after you create the GitHub repo — see "Push to GitHub" at bottom)
git clone https://github.com/barnes-ngb/compass.git
cd compass

# 2. Per-user venv
py -3.11 -m venv .venv

# 3. Activate (if execution policy blocks: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned — no admin needed)
.\.venv\Scripts\Activate.ps1

# 4. Dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 5. Install compass itself (editable). This is what makes `python -m compass` resolve.
pip install -e .

# 6. Config
Copy-Item .env.example .env
notepad .env   # paste ANTHROPIC_API_KEY
```

> **Why step 5 matters:** compass uses a `src/` layout. Without `pip install -e .`, Python doesn't know where to find the `compass` package and `python -m compass` fails with `No module named compass`. The `-e` flag means "editable" — your code edits are picked up immediately, no reinstall needed.

---

## Run

**Visual mode (Phase 0 — works today):**

```powershell
python -m compass --mode visual
```

Two windows open: webcam preview + simulated HUD. SPACE captures, ESC quits.

**Verbal and retro modes (Phase 2 — stubs only):**

```powershell
python -m compass --mode verbal    # raises NotImplementedError
python -m compass --mode retro     # raises NotImplementedError
```

These will light up once we wire STT and the rolling audio buffer.

**Fully offline:** set `VISION_PROVIDER=mock` in `.env` — no API calls, canned responses.

---

## Project layout

```
src/compass/
├── __main__.py           Entry point: `python -m compass`
├── cli.py                Wire config → providers → pipeline
├── config.py             .env loader
├── pipeline.py           Mode-aware orchestration: visual / verbal / retro
├── glasses/              Hardware abstraction (Phase 0 mock; Phase 1 real)
│   ├── base.py           Glasses Protocol
│   ├── mock.py           OpenCV webcam + simulated HUD
│   └── frame.py          Stub — real Brilliant Labs Frame
├── vision/               Image → directive
│   ├── base.py           VisionProvider Protocol
│   ├── claude.py         Anthropic Claude
│   ├── gemini.py         Stub
│   └── mock.py           Canned responses
├── coach/                Transcript + memory + intent → directive
│   ├── base.py           CoachProvider Protocol
│   ├── claude.py         Anthropic Claude
│   └── mock.py           Canned coach responses
├── audio/                Capture and STT for retro mode
│   ├── buffer.py         Rolling buffer (interface only, no capture yet)
│   └── stt.py            Whisper STT (interface only, no inference yet)
└── memory/               Layered memory store
    └── store.py          SQLite-backed; sessions, summaries, digests
```

---

## Push to GitHub

The repo doesn't exist on GitHub yet. Two options:

**A — GitHub CLI** (if installed; `winget install GitHub.cli` works without admin in user scope):

```powershell
cd path\to\compass
git init
git add .
git commit -m "Phase 0: project scaffold and mock pipeline"
gh auth login   # once
gh repo create barnes-ngb/compass --public --source=. --remote=origin --push
```

**B — Web UI:**

1. Create empty repo at https://github.com/new (owner `barnes-ngb`, name `compass`, no README/license).
2. Then:
```powershell
cd path\to\compass
git init
git add .
git commit -m "Phase 0: project scaffold and mock pipeline"
git branch -M main
git remote add origin https://github.com/barnes-ngb/compass.git
git push -u origin main
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `No module named compass` when running `python -m compass` | You skipped step 5. Run `pip install -e .` in the activated venv. |
| Venv activation blocked | `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` (no admin needed) |
| Webcam black frame | Close Teams/Zoom/OBS; or set `CAMERA_INDEX=1` |
| `anthropic.AuthenticationError` | Check `ANTHROPIC_API_KEY` starts with `sk-ant-` |
| OpenCV fails on Python 3.13 | Use 3.11 or 3.12 — wheels lag |
| Tkinter window doesn't show | Reinstall Python with tcl/tk checked |

---

## License

MIT. Add `LICENSE` after first push.
