# 0006 — Layered memory pipeline + tap-to-tap V0 sessions

**Status:** Accepted · **Date:** 2026-05-19

## Context

A coach is just a tool unless it remembers. The lived question "what did we decide about steel grade last Tuesday?" needs memory at four time scales: seconds (just-now), hours (this meeting), days (last week), months (this project).

A single rolling audio buffer doesn't solve this — it's a tape recorder, and tape recorders are not coaches. The value is in the *synthesis layer*, where raw moments compress into summaries that compress into digests that compress into project memory.

We also need a session model: when does a conversation start, when does it end, and what's persisted vs. discarded. Three candidate models:

1. **Opt-in, tap-to-tap.** User explicitly starts and stops a session. Simple, robust, requires discipline.
2. **Tap-to-start with auto-end heuristics.** User taps to start; the system ends the session on silence, calendar end-time, or context switch. More forgiving.
3. **Always-armed with topic segmentation.** Buffer is always running; sessions are auto-detected by topic boundaries. Magical and fragile.

Each requires different infrastructure. Picking the wrong one strands engineering effort.

## Decision

### The memory pipeline (all phases)

```
Live audio  →  Rolling buffer (last 30 min, RAM-only, NEVER persisted)
                    ↓ on button-press OR session-end
            Session transcript (full STT, persisted)
                    ↓ summarized at session-end
            Session summary (key points, decisions, open questions)
                    ↓ rolled up nightly
            Daily digest (themes, commitments, references)
                    ↓ rolled up over time
            Project memory (recurring threads, your stated goals)
```

Each layer is independently useful. Each compresses the layer below it. Query interface is uniform across layers — same `CoachProvider`, different `memory_context` payload.

**Retention policy:**
- **Raw audio bytes**: discarded immediately after STT. Never written to disk.
- **Transcripts**: retained indefinitely in `MemoryStore` (SQLite, local).
- **Summaries, digests, project memory**: retained indefinitely.
- **No cloud sync.** Database is a file on the user's laptop.

### Session model: phased V0 → V1 → V2

| Version | Model | Rationale |
|---|---|---|
| **V0** | Tap to tap. User starts and ends every session explicitly. | "What counts as a session?" is empirically unknown until we use V0 for two weeks. Don't engineer heuristics for behavior we haven't observed. |
| **V1** | Tap to start + auto-end heuristics (silence > N min, calendar end-time, context switch). | Once V0 has produced data on actual session shapes, we can tune end-detection without guessing. |
| **V2** | Always-armed + topic segmentation. Rolling buffer always running; sessions auto-detected at topic boundaries. | The hardest version. Build only after V0 + V1 have answered the empirical question. |

### The ethical and architectural boundary

Compass processes **the user's own working memory of conversations the user is in**. It is:
- *Not* a continuous recorder.
- *Not* a surveillance tool for other people.
- *Not* a meeting-bot that records meetings the user isn't attending.

The rolling buffer is RAM-only. The only persistent artifact from audio is text, and only after the user explicitly invokes the Retro mode (or sessions end with summarization in V1+). In US two-party-consent states, this is the difference between *processing your own perception of a conversation you're in* and *recording the conversation* — the former is uncontroversial, the latter is not.

## Consequences

**Good:**
- Memory at four time scales without four memory systems. One SQLite file, one schema, four query patterns.
- V0 ships fast. Tap-to-tap is the simplest possible session model and gives us real usage data.
- The "creepy" failure mode is architecturally impossible: no continuous recording, no cloud sync, no surveillance of third parties.
- Layered memory lets the coach answer at the right zoom level without re-reading hours of transcript every query.

**Bad:**
- User discipline required in V0. If you forget to tap "end," the session runs forever or until you next remember. Mitigation: V1 heuristics. Living-with-it cost in the interim: low.
- Summary quality is bounded by the LLM's summary quality. Compounding loss across layers (session → daily → project). Mitigation: store the raw transcript so we can re-summarize with better prompts later.
- SQLite means no concurrent access. Two compass processes would corrupt the DB. Single-user, single-process is the design.

## Alternatives considered

- **Vector embeddings from day one.** Rejected for V0: adds an embedding service dependency and a retrieval-tuning problem before we have any data to retrieve. Keyword + recency suffices. Embeddings (`sqlite-vec`) wire in later when retrieval quality demands.
- **Cloud-sync database.** Rejected: privacy posture is the differentiator. Local-only is the architectural commitment. Sync (encrypted, opt-in) is a possible future feature, not a V0 default.
- **Continuous audio recording with later opt-out.** Rejected on first principles. The rolling buffer is RAM-only and that's the architectural line.
- **Topic-bounded sessions from V0.** Rejected. Building topic-segmentation infrastructure before we know what topic boundaries look like in practice is over-engineering.

## Triggers to advance V0 → V1

| Signal | Action |
|---|---|
| Compass used in ≥ 5 real sessions over 2 weeks | Audit: did we remember to tap "end"? What did the misses look like? |
| Sessions average > 90 min because of forgotten end-tap | Add silence-based auto-end as first heuristic. |
| Memory store > 100 MB | Add archive-and-prune tooling. |

## Postscript: 2026-06-12 — V0 implemented as run-as-session

The V0 session model above specifies "tap to tap: user starts and ends every session explicitly." Phase 1b implemented that explicit boundary as run-as-session: one `python -m compass` run is one session. `start_session` fires after the glasses connect, every event in the run carries that `session_id`, and on loop exit the transcript is assembled from the run's events and a summary is written. Verbal and retro summarize through the coach; visual stores the transcript without an LLM summary, since a batch of one-shot image lookups does not compress usefully in V0.

Why program lifetime rather than an in-loop session key: the `Glasses` trigger returns a bare bool, trigger versus quit, with no room for a third "toggle session" signal. An in-loop key would have forced a change to the `Glasses` Protocol, which the rest of the system deliberately keeps narrow. Program launch and quit are already explicit, user-controlled acts, so they satisfy the V0 principle without new Protocol surface.

This does not change the V0 to V1 to V2 progression or the advancement triggers above. Once run-as-session produces real data on how long runs last and how often a run is left open, silence-based auto-end becomes the first V1 heuristic. The V0 transcript is assembled from the event log; continuous-STT session transcripts remain a later concern tied to the always-armed V2 model.
