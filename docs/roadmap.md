# compass — Roadmap

Phased, with explicit exit criteria. Each phase is shippable on its own; no phase blocks on the next.

> **Restructured 2026-06-12.** Hardware (Halo) realistically lands late Q3 / Q4 2026, and the build already proved the modes ship on laptop hardware first: the rolling buffer and retro mode landed before any glasses existed. Phases now follow that reality — software modes complete on laptop, then the Halo wire-in. Latency budgets follow ADR 0009. The pre-restructure roadmap is in git history.

---

## Phase 0 — Scaffold + mock visual pipeline ✅ Complete

**Goal:** end-to-end visual mode running against a mock, every architectural piece in place.

**Done:**
- Project scaffold (`src/compass/`, `docs/`, `tests/`)
- `Glasses` Protocol + `MockGlasses` driver (webcam + cv2 HUD)
- `VisionProvider` Protocol + `ClaudeVision` + `MockVision`
- `CoachProvider` Protocol + `ClaudeCoach` + `MockCoach` (stubs at the time; both real now)
- `MemoryStore` SQLite layer (events table working; sessions + digests scaffolded)
- `pipeline.run_visual` working end-to-end
- Founding ADRs 0001–0007 (0008–0009 followed during Phase 1)

**Exit criteria (met):**
- `python -m compass --mode visual` runs against laptop webcam + cv2 HUD without errors.
- `MockVision` returns canned responses with no API key.
- `tests/test_smoke.py` passes.
- README documents setup, run, and project layout accurately.
- Project pushed to `github.com/barnes-ngb/compass`.

---

## Phase 1 — All three modes on laptop ← Current

**Goal:** visual, verbal, and retro all lit on laptop hardware; layered memory working; real usage data captured. No glasses required.

**Done:**
- **Rolling audio buffer** — `LaptopMicBuffer` (`sounddevice` + numpy ring buffer). RAM-only by design (ADR 0006).
- **Retro mode V0 (tap-to-tap)** — `pipeline.run_retro` end-to-end: trigger → buffer snapshot → STT → `CoachProvider.respond` → HUD. First real end-to-end test 2026-05-20.
- **Real local STT** — `WhisperSTT` via `faster-whisper`, default `small.en` (`base.en` mangled shop vocabulary — "facade panels" → "sign tables"). Cloud STT (e.g., Deepgram) remains an option if verbal-mode latency demands it.
- **Measured baseline** — retro press-to-HUD currently 12–22 s on laptop. Within ADR 0009's budget.

**Remaining:**

### 1a — Verbal mode
- Wire `pipeline.run_verbal` end-to-end: trigger → mic capture → STT → `CoachProvider.respond` → HUD.
- Trigger: laptop hotkey on mock (button-press on glasses later). Pull-default; no wake word (ADR 0005).
- Latency target: ≤ 10 s press-to-HUD on laptop. Short-utterance STT is far cheaper than retro's buffer transcription. Measure and record actuals.

### 1b — Session lifecycle (V0, tap-to-tap)
- Explicit `start_session` / `end_session` affordance.
- On session end: STT the full session, summarize, store in `sessions.transcript` + `sessions.summary`.

### 1c — Daily digest rollup
- Nightly job (Windows Task Scheduler) summarizing the day's sessions into `daily_digests`.
- CLI: `python -m compass digest --date 2026-06-12` for ad-hoc runs.

### 1d — Privacy audit
- File-system audit confirming no raw audio bytes ever touch disk (ADR 0006 invariant).

**Exit criteria:**
- All three modes lit and tested on laptop.
- Two weeks of real V0 session data captured.
- Audit: how often did we forget to end a session? What did the misses look like?
- Decision recorded: V1 heuristics worth building, or is tap-to-tap fine?

---

## Phase 2 — Halo wire-in

**Goal:** the abstraction survives contact with real glasses. Hardware path per ADR 0008 (Halo primary, Frame backup, no committed fallback); implementation strategy per ADR 0009 (Python host + minimal Lua).

**Pre-arrival (can run in parallel with Phase 1):**
- Design pass against the published SDK (`brilliant-msg` + `brilliant_sdk` examples):
  - `HaloGlasses` skeleton mapping the 5-method `Glasses` Protocol onto `brilliant-msg`.
  - `halo.lua` reflex sketch (~50–100 lines: button → notify host; host message → render).
  - API gap list — what compass needs that the SDK doesn't expose.
  - Latency budget analysis: BLE round-trip + JPEG capture + cloud Claude.
  - First-hour playbook (`docs/halo-wireup.md`): what to do the day hardware arrives.
- Sketches stay out of the repo until hardware arrives (per ADR 0009 and AGENTS.md: no speculative stubs, no `brilliant-msg` dependency yet).

**On arrival:**
- Implement `src/compass/glasses/halo.py` + `src/compass/glasses/halo.lua` (locations per ADR 0009 §6). Lua uploads on `Glasses.connect()`.
- Add `brilliant-msg` to dependencies — only now (ADR 0009).
- Side-by-side: same pipeline, same prompt, mock vs. Halo. Document latency deltas.
- Update `docs/landscape.md` with what integration taught us.
- If a used Frame appears first (passive eBay watch), `glasses/frame.py` via `frame-msg` becomes an optional early checkpoint, not a commitment.

**Exit criteria:**
- `python -m compass --mode visual --glasses halo` runs end-to-end on hardware; all three modes follow.
- Measured latencies recorded against ADR 0009 budgets (visual ~5–10 s, retro ~12–22 s). A blown budget fires ADR 0009's re-evaluation trigger — a decision point, not a silent failure.
- `MockGlasses` still works — we didn't break the abstraction.
- A demo video (60 s) lands on the portfolio site.

---

## Phase 3 — V1 sessions + domain-specific coach personas

**Goal:** the coach gets smarter about *when* to speak and *what* it knows.

### 3a — V1 session model
- Auto-end heuristics: silence > 5 min, calendar end-time, context switch (Bluetooth device change, geofence).
- Each heuristic configurable, default-on or default-off based on Phase 1's V0 audit data.

### 3b — Push channels (narrow, opt-in)
- Scheduled: calendar-driven nudges ("you said you'd review the Zahner drawings at 2pm").
- Threshold: "you've been on this query for 20 minutes, want a hint?"
- Each push channel is opt-in per user.

### 3c — Domain personas
- **Fabrication coach** — wired to a local knowledge base of shop reference docs (perforation patterns, weathering steel specs, anchor specs).
- **Knowledge coach** — generalist, uses retrieval over the user's project notes.
- **Life coach** — gentle, calendar-aware, memory-aware. Reminds you of stated goals.

Personas are configurable via env (`COACH_PERSONA=fabrication`) and behind a single `CoachProvider` interface so they're swappable.

### 3d — Embeddings + semantic search
- Add `sqlite-vec` or `chromadb` for transcript and summary search.
- Improve retrieval quality on "what did we decide about X" queries.

**Exit criteria:**
- A "fabrication coach" persona answers shop-specific questions with retrieval-grounded responses.
- Cross-session recall demonstrably better than keyword-only baseline.
- Portfolio page updated with at least one real workflow video (not a mock demo).

---

## Phase 4+ — Open questions

Deferred until earlier phases produce real usage data:

- **Phone-as-BLE-bridge mobility** (ADR 0009 §5) — build when laptop tethering blocks a use case the user actually wants (likely "walking the shop while compass is alive"). Estimated 2–3 weeks; all Python stays server-side.
- **V2 always-armed sessions** with topic segmentation — only if V1 tap-and-heuristics proves inadequate.
- **Second-vendor coach** (Gemini, GPT-5) for redundancy.
- **Cloud sync** of MemoryStore — encrypted, opt-in, for multi-device users.
- **On-device models** — Halo's NPU is not exposed to third-party models today (ADR 0009 §4); revisit if Brilliant ships a loader. Phone-NPU VLMs (Moondream 2, Qwen2.5-VL-3B) likewise wait for viability.
- **Industrial driver** (Vuzix M400 / RealWear) — only when a real Zahner pilot crystallizes.

---

## Backlog (unsorted, low-priority)

- Prescription lens fitting workflow (Frame partner Smart-Buy-Glasses, or Even Realities G1 path).
- Streaming responses (token-by-token render on HUD) instead of wait-for-complete.
- Multi-image visual mode (capture sequence, ask about set).
- "Coach reflection" — weekly summary of what the coach got wrong, to tune prompts.
- A `compass-cli` standalone command separate from `python -m compass` for shorter invocations.
- Color theming for the HUD (current: cv2 green; real: device-dependent).
