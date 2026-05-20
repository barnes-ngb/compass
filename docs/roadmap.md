# compass — Roadmap

Phased, with explicit exit criteria. Each phase is shippable on its own; no phase blocks on the next.

---

## Phase 0 — Scaffold + mock visual pipeline ✅ Current

**Goal:** end-to-end visual mode running against a mock, every architectural piece in place.

**Done:**
- Project scaffold (`src/compass/`, `docs/`, `tests/`)
- `Glasses` Protocol + `MockGlasses` driver (webcam + cv2 HUD)
- `VisionProvider` Protocol + `ClaudeVision` + `MockVision`
- `CoachProvider` Protocol + `ClaudeCoach` + `MockCoach` (stubs ready)
- `MemoryStore` SQLite layer (events table working; sessions + digests scaffolded)
- `pipeline.run_visual` working end-to-end
- All seven ADRs written

**Exit criteria:**
- `python -m compass --mode visual` runs against laptop webcam + cv2 HUD without errors.
- `MockVision` returns canned responses with no API key.
- `tests/test_smoke.py` passes.
- README documents setup, run, and project layout accurately.
- Project pushed to `github.com/barnes-ngb/compass`.

---

## Phase 1 — First real hardware driver

**Goal:** the abstraction survives contact with real glasses.

**Tasks:**
- Acquire a device (per `docs/decisions/0004-hardware-strategy.md`):
  - Primary: used Brilliant Labs Frame H20 from eBay (saved-search alert active)
  - Fallback at 30 days: Vuzix Z100 + Mentra Live pair
- Implement the corresponding driver in `glasses/`:
  - `glasses/frame.py` — wire `frame-msg` (CitizenOne community SDK)
  - or `glasses/z100.py` — wire Vuzix Ultralite SDK via a small Kotlin/Python bridge
- Side-by-side comparison: same pipeline, same prompt, mock vs. real. Document latency delta.
- Update `docs/landscape.md` with what we learned during integration.

**Exit criteria:**
- `python -m compass --mode visual --glasses frame` (or equivalent) runs end-to-end on real hardware.
- Total interaction latency ≤ 3 s on real device, measured with the same prompt as mock.
- A demo video (60 s) lands on the portfolio site.
- `MockGlasses` still works — we didn't break the abstraction.

---

## Phase 2 — Verbal + Retro modes

**Goal:** voice and retrospective modes lit up; layered memory beyond the events table.

**Tasks:**

### 2a — Verbal mode
- Wire `audio/stt.py` to a real STT (recommended: `faster-whisper` with `base.en` model, local on Windows; cloud Deepgram as fallback for latency-sensitive cases).
- Hardware trigger: button-press on glasses (or laptop hotkey on mock).
- `pipeline.run_verbal` end-to-end: trigger → mic capture → STT → `CoachProvider.respond` → HUD.
- Latency budget: ≤ 3 s total.

### 2b — Rolling audio buffer
- Wire `audio/buffer.py` to capture from the default input device into a 30-min ring buffer.
- RAM-only, never written to disk. Verify with a file-system audit.
- Configurable window length (5 / 15 / 30 min).

### 2c — Retro mode (V0 session model: tap-to-tap)
- `pipeline.run_retro` end-to-end: button-press → buffer snapshot → STT → `CoachProvider.respond(intent, transcript, memory_context)` → HUD.
- Session lifecycle: explicit `start_session` / `end_session` via a UI affordance.
- On session end: STT the full session, summarize, store in `sessions.transcript` + `sessions.summary`.

### 2d — Daily digest rollup
- Nightly job (Windows Task Scheduler) that summarizes the day's sessions into `daily_digests`.
- CLI: `python -m compass digest --date 2026-05-19` for ad-hoc.

**Exit criteria:**
- All three modes lit and tested.
- Two weeks of real V0 session data captured.
- Audit: how often did we forget to end a session? What did the misses look like?
- Decision: V1 heuristics worth building, or is tap-to-tap fine?

---

## Phase 3 — V1 sessions + domain-specific coach personas

**Goal:** the coach gets smarter about *when* to speak and *what* it knows.

**Tasks:**

### 3a — V1 session model
- Auto-end heuristics: silence > 5 min, calendar end-time, context switch (Bluetooth device change, geofence).
- Each heuristic configurable, default-on or default-off based on V0 data.

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

- **V2 always-armed sessions** with topic segmentation — only if V1 tap-and-heuristics proves inadequate.
- **Second-vendor coach** (Gemini, GPT-5) for redundancy.
- **Cloud sync** of MemoryStore — encrypted, opt-in, for multi-device users.
- **On-device VLM** (Moondream 2, Qwen2.5-VL-3B) for offline visual mode — when phone NPUs make this viable.
- **Industrial driver** (Vuzix M400 / RealWear) — only when a real Zahner pilot crystallizes.

---

## Backlog (unsorted, low-priority)

- Prescription lens fitting workflow (Frame partner Smart-Buy-Glasses, or Even Realities G1 path).
- Streaming responses (token-by-token render on HUD) instead of wait-for-complete.
- Multi-image visual mode (capture sequence, ask about set).
- "Coach reflection" — weekly summary of what the coach got wrong, to tune prompts.
- A `compass-cli` standalone command separate from `python -m compass` for shorter invocations.
- Color theming for the HUD (current: cv2 green; real: device-dependent).
