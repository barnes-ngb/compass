# compass — Architecture

## One-line

A glance-paced AI coach with persistent layered memory. Hardware-abstracted. Three modes (visual, verbal, retro) share one backend.

## Modules

| Module | Responsibility |
|---|---|
| `compass.cli` | Parse `--mode`, load config, build providers, dispatch to a `run_*` function |
| `compass.config` | Single dataclass loaded from `.env`. No env-fiddling anywhere else |
| `compass.pipeline` | Three top-level orchestrators: `run_visual`, `run_verbal`, `run_retro`. Phase 0 implements visual; verbal and retro raise `NotImplementedError` |
| `compass.glasses` | Hardware abstraction. `Glasses` Protocol: `connect / wait_for_trigger / capture_image / show_text / close`. Drivers: `MockGlasses` (webcam + cv2 HUD), `FrameGlasses` (Phase 1 stub) |
| `compass.vision` | Image → directive. `VisionProvider.describe(bytes, prompt) -> str`. Implementations: `ClaudeVision`, `MockVision`, `GeminiVision` (stub) |
| `compass.coach` | Transcript + memory + intent → directive. `CoachProvider.respond(intent, transcript, memory_context) -> str`. Implementations: `ClaudeCoach`, `MockCoach` |
| `compass.audio` | Rolling audio buffer + STT. `RollingBuffer` and `STT` protocols. Phase 2 stubs |
| `compass.memory` | SQLite-backed layered memory. Tables: `events`, `sessions`, `daily_digests`. Rollup logic is Phase 2 |

## The three modes

### Visual (Phase 0 — works today)

```
tap → camera capture → VisionProvider.describe(image, prompt) → HUD
```

Sibling to scan-to-action. The user points at something, asks a quick question, and gets a glance-sized answer in their right eye. Every event is logged to memory so it's queryable later.

Latency budget: 1.5–3 s for cloud VLM (Claude Sonnet 4.6). 0 s for `MockVision`.

### Verbal (Phase 2 — stub)

```
voice trigger → STT(now) → CoachProvider.respond(query, transcript="") → HUD
```

"Hey compass, what does ASTM A606 mean?" The verbal mode is essentially Visual without the image — it goes through the coach (text-only) rather than vision (image+text). Memory context can be retrieved to ground the answer in your projects.

Latency budget: 0.5–1.5 s (STT) + 0.5–1.5 s (coach) = 1–3 s total.

### Retro (Phase 2 — stub)

```
button-press → RollingBuffer.snapshot(last_N_min) → STT → CoachProvider.respond(intent, transcript) → HUD
```

The killer mode. The rolling audio buffer is always armed during a session (RAM-only, never persisted). On button-press, the last N minutes are transcribed and fed to the coach with current memory context. The coach returns a short HUD directive: *"they asked about Q3 panel schedule"* or *"decided 16-ga weathering steel."*

Latency budget: 2–4 s (STT of a 5-min buffer is the long pole on local Whisper; cloud STT cuts this to ~1 s).

## Layered memory pipeline

```
Live audio        (in-glasses mic or phone mic, Phase 2)
    │
    ▼
Rolling buffer    (RAM only, NEVER persisted, 30-min default window)
    │   button-press OR session-end
    ▼
Session transcript     (text, persisted to memory.sessions.transcript)
    │   summarized at session-end
    ▼
Session summary        (text, persisted to memory.sessions.summary)
    │   rolled up nightly
    ▼
Daily digest           (text, persisted to memory.daily_digests)
    │   queryable on demand
    ▼
Project memory         (recurring threads, your stated goals — Phase 3)
```

Each layer is cheap to build (a prompt + a storage row), and each is independently useful. Phase 0 implements `events` (the lowest persistent layer). Sessions, summaries, and digests come online with Phase 2.

**Retention policy**: raw audio bytes are discarded immediately after STT. Transcripts and summaries are retained indefinitely (it's your data, on your machine). Compass never records continuously — the rolling buffer only runs during an explicit session.

## Latency budget for a "glanceable" interaction

The whole loop must feel like checking your watch. Total ≤ 2.5 s desktop / ≤ 3 s on Frame.

| Stage | Mock | Real (cloud Sonnet 4.6) |
|---|---|---|
| Capture | 30 ms (cv2.read + imencode) | 200–400 ms (BLE JPEG @ Frame) |
| Network upload | 0 | 100–400 ms |
| Model inference | 0 | 800–1500 ms |
| Render to HUD | 5 ms (cv2.imshow) | 100 ms (BLE) |
| **Total** | **~50 ms** | **~1.5–2.5 s** |

Stays within the "glance" budget. If we ever miss, the bottleneck is almost always the VLM, not the transport.

## Why a Protocol, not an ABC

Mock and real drivers don't need to share an ancestor. Third-party drivers (community Frame SDK, future Halo SDK, Mentra TypeScript bridge) can be dropped in via duck-typing. The `@runtime_checkable` decorator means `isinstance(x, Glasses)` still works.

## Why mode dispatch in `cli.py` instead of a "mode" object

YAGNI. Three top-level entry points (`run_visual`, `run_verbal`, `run_retro`) is less abstraction than a `Mode` strategy class, and the modes diverge enough that the shared code would mostly be the imports. Re-evaluate if we add a fourth mode.

## What doesn't belong in compass

- AR overlay / marker tracking. That's scan-to-action's problem. Compass is glance-paced and frame-by-frame, not registered AR.
- Continuous recording. Hard architectural line. The rolling buffer is RAM-only.
- Surveillance of others. Compass processes the user's own working memory of conversations they participate in. See `docs/decisions/0006-memory-layers.md`.
