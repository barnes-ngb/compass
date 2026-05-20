# 0005 — The three coach modes and their shared backend

**Status:** Accepted · **Date:** 2026-05-19

## Context

The original "glance-to-directive" framing was a single-mode product: tap → camera → VLM → HUD. Useful but narrow. The actual lived problem is broader — *"understand my world better, don't miss things, get insight from the wealth of knowledge plus me."*

That lived problem spans:
- *Visual* questions: "what is this?", "does this match the drawing?", "how do I bend this radius?"
- *Verbal* questions out of nowhere: "what does ASTM A606 mean?", "remind me what we decided last Tuesday?"
- *Retrospective* questions about a conversation already happening: "what did they just ask?", "summarize the last 10 minutes", "what did we agree on?"

The temptation is to build three separate products. The opportunity is to recognize they share *almost everything*: hardware abstraction, memory, LLM provider, output rendering. They diverge only in input source.

## Decision

One product, three modes, one backend.

### The three modes

| Mode | Trigger | Input | Pipeline component |
|---|---|---|---|
| **Visual** | tap (glasses) / SPACE (mock) | camera frame | `VisionProvider.describe(image, prompt)` |
| **Verbal** | voice wake word (Phase 2) | mic, ~5 s | `STT` → `CoachProvider.respond(intent, "", memory)` |
| **Retro** | button-press (long hold) | rolling buffer, last N min | `STT` → `CoachProvider.respond(intent, transcript, memory)` |

All three:
- Share the same `Glasses` driver for output.
- Log to the same `MemoryStore`.
- Use the same Anthropic API key and model (configurable per-mode if needed).
- Return a short HUD directive (≤ 28 chars per line, two lines max).

### Trigger philosophy: pull-default, narrow push

Compass speaks when invoked. Three explicit push channels are reserved for V1+:
1. **Scheduled** — calendar nudges, time-of-day reminders.
2. **Threshold** — "you've been on this for 20 minutes, want a hint?"
3. **Acute hazard** — safety/health (e.g., posture if biometrics ever wire in).

No ambient meeting-listener, no surprise notifications. The user controls when compass speaks.

### Why these three, not more, not fewer

- **Visual without Verbal** loses the "what does X mean?" use case that doesn't have an image. Bad.
- **Verbal without Retro** misses the unique value: catching what was just said when you were thinking about something else. The Retro mode is the only mode that has no good non-glasses substitute (you can ask Claude on a laptop, but not while sitting in the conversation).
- **A fourth always-on mode** is the failure mode of every AI-pin product. Explicitly rejected.

## Consequences

**Good:**
- Same protocols, same memory, same provider keys. Adding a mode is adding an entry point, not a subsystem.
- Mode boundaries map onto V0 → V1 → V2 phasing. Visual is done today; Verbal needs STT-on-demand; Retro needs the rolling buffer and the session model. Clear backlog.
- The "coach" personality is unified across modes. A user shouldn't have to learn three tools.

**Bad:**
- The `CoachProvider.respond(intent, transcript, memory_context)` interface is wider than `VisionProvider.describe(image, prompt)`. More surface area to test.
- Mode dispatch in `cli.py` is currently a `match` on `--mode`. If we add a fourth mode, the dispatch grows. Acceptable for three; revisit at five.

## Alternatives considered

- **Three separate CLIs / repos.** Rejected: duplication of memory, config, Glasses driver. The shared backend is the whole point.
- **One mode (Visual only).** Rejected: misses the retrospective use case, which is the most distinctive thing compass can do.
- **Always-on ambient listener as a fourth mode.** Rejected on UX grounds (notification fatigue) and on ethical grounds (surveillance posture). The button-gated Retro mode delivers most of the same value with none of the cost.

## Open questions, deferred

- Does Verbal really need a voice wake-word, or is a hardware-button press (same as Retro) a cleaner UX? Defer to Phase 2 testing.
- Is there a fifth pattern — "scheduled" or "background-summarize" — that should become its own mode? Defer until we've used V0 + V1 enough to know.
