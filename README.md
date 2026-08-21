# compass

> An AI coach that helps me understand my world better and not miss things — pull-default, glance-paced, with persistent layered memory.

`compass` is a wearable AI coach. Three modes share one backend:

- **Visual** — tap → camera capture → "what is this?" / "does this match the drawing?" → directive on HUD.
- **Verbal** — voice trigger → ask anything → directive on HUD.
- **Retro** — button-press → process the last N minutes of conversation buffer → "what did they just ask?" / "summarize the last 10 min" / "what did we decide?"

All three feed and draw from a **layered, lossy memory pipeline** — rolling audio buffer → session transcript → session summary → daily digest → project memory — so compass can answer at any zoom level from "five minutes ago" to "what's the through-line of the Zahner project."

The hardware is abstracted. Today the visual mode runs against a mock (laptop webcam + simulated HUD window) so the whole pipeline is built and iterated before any glasses arrive. When real hardware ships, only the driver in `src/compass/glasses/` changes.

This project is the glance-paced field surface for the directive family — the deviation and directive computation live in [directive-engine](https://github.com/barnes-ngb/directive-engine) (built), with [scan-to-action](https://github.com/barnes-ngb/scan-to-action) reserved as the future scan-side ingest layer (not yet implemented). See `docs/portfolio-fit.md`.

---

## Thesis

> *"Understand my world better, don't miss things, get insight from the wealth of knowledge plus me."*

Pull-default — compass speaks when invoked, not when it feels like it. Persistent memory — it knows my projects, my goals, my patterns over time. Layered — it can answer about five minutes ago or five months ago using the same prompt surface. Honest about its boundaries — processes my own working memory of conversations I'm in, never records continuously, never surveils others.

---

## Status

- ✅ Phase 0: project scaffold, mock visual pipeline, three-mode architecture
- ⏳ Phase 1: real hardware integration (see `docs/landscape.md`)
- 🟡 Phase 2: all three modes — visual, verbal, and retro — wired end-to-end (real mic + local Whisper STT + Claude coach); memory rollup layers pending
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
| `docs/decisions/0008-hardware-path.md`     | Halo primary, Frame backup, no committed fallback — current hardware decision |
| `docs/decisions/0009-halo-language-strategy.md` | Python host + minimal Lua, phone deferred — current implementation strategy |
| `web/compass.md` | Draft Astro page for the portfolio site |

---

## Requirements

- Windows 10/11 (PowerShell 5.1+ or 7)
- Python 3.11 or newer (tested on 3.11, 3.12, 3.13)
- A webcam (built-in is fine)
- An Anthropic API key — https://console.anthropic.com/

No admin rights. No Docker. No global installs.

---

## Setup (PowerShell)

```powershell
# 1. Clone
git clone https://github.com/barnes-ngb/compass.git
cd compass

# 2. Per-user venv
py -3 -m venv .venv

# 3. Activate (if execution policy blocks: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned — no admin needed)
.\.venv\Scripts\Activate.ps1

# 4. Dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 5. Install compass itself (editable). This is what makes `python -m compass` resolve.
pip install -e .

# To enable real audio capture for verbal + retro modes: pip install -e ".[audio]"
# For development (tests + lint + real audio): pip install -e ".[dev,audio]"

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

**Retro mode (Phase 2 — works today):**

```powershell
# In .env (or per-session): AUDIO_BUFFER=laptop and STT_PROVIDER=whisper
python -m compass --mode retro
```

The HUD simulator opens; the rolling mic buffer runs in RAM. SPACE transcribes
the last 5 minutes and asks the coach; ESC quits. The audio defaults
(`AUDIO_BUFFER=mock`, `STT_PROVIDER=mock`) use canned audio; add
`COACH_PROVIDER=mock` to run fully offline with no API calls. First whisper run
downloads the `small.en` model (~244 MB, cached thereafter).

**Verbal mode (Phase 2 — works today):**

```powershell
# In .env (or per-session): AUDIO_BUFFER=laptop and STT_PROVIDER=whisper
python -m compass --mode verbal
```

Press SPACE, *then* speak your question. The HUD shows "Listening..." for a
fixed window (`VERBAL_CAPTURE_SECONDS`, default 8), transcribes what you said,
and asks the coach — your speech is the query. The preceding two minutes of
buffer go along as conversational context. Same `AUDIO_BUFFER` /
`STT_PROVIDER` / `COACH_PROVIDER` settings as retro; ESC quits.

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
├── audio/                Capture and STT for verbal + retro modes
│   ├── buffer.py         RollingBuffer Protocol + Null/Mock implementations
│   ├── laptop_mic.py     Real capture — sounddevice + numpy ring buffer (RAM only)
│   ├── stt.py            STT Protocol + Null/Mock implementations
│   └── whisper_stt.py    Real local STT — faster-whisper, default small.en
└── memory/               Layered memory store
    └── store.py          SQLite-backed; sessions, summaries, digests
```

---

## Branching workflow

Updates land via PRs, not pushes to main. Two ways to make changes:

**Locally** — branch from main, edit, push, open a PR:

```powershell
git checkout -b feature/short-description
# ...edit...
git add . ; git commit -m "concise message"
git push -u origin feature/short-description
gh pr create --fill   # or open in the GitHub web UI
```

**Via Claude Code web** — prompt Claude with the change you want; it opens a PR on a `claude/<short-description>` branch for review.

Either way, every change is one branch, one PR, reviewed before merge.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `No module named compass` when running `python -m compass` | You skipped step 5. Run `pip install -e .` in the activated venv. |
| Venv activation blocked | `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` (no admin needed) |
| Webcam black frame | Close Teams/Zoom/OBS; or set `CAMERA_INDEX=1` |
| `anthropic.AuthenticationError` | Check `ANTHROPIC_API_KEY` starts with `sk-ant-` |
| Whisper mistranscribes shop vocabulary | Default is `small.en`; if speed matters more than accuracy, set `WHISPER_MODEL=base.en`. For better accuracy still, see ADR 0006 about cloud STT options. |
| Tkinter window doesn't show | Reinstall Python with tcl/tk checked |

---

## License

MIT — see [LICENSE](LICENSE).
