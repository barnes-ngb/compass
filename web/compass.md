---
layout: ../../../layouts/Work.astro
title: compass
slug: compass
order: 4
summary: A pull-default, glance-paced AI coach with persistent layered memory. Sibling to scan-to-action.
status: in-progress
tech: Python · Anthropic Claude · OpenCV · SQLite · smart-glasses HUD
repo: https://github.com/barnes-ngb/compass
hero: /img/work/compass-hero.png
---

> *Understand my world better, don't miss things, get insight from the wealth of knowledge plus me.*

## What it is

Compass is a wearable AI coach. Three modes share one backend:

- **Visual** — tap → camera capture → "what is this?" / "does this match the drawing?" → directive on HUD.
- **Verbal** — voice trigger → ask anything → directive on HUD.
- **Retro** — button-press → process the last N minutes of conversation buffer → "what did they just ask?" / "summarize the last 10 min" / "what did we decide?"

All three feed and draw from a **layered, lossy memory pipeline** — rolling audio buffer → session transcript → session summary → daily digest → project memory — so compass can answer at any zoom level from "five minutes ago" to "what's the through-line of the Zahner project."

## How it fits

Compass is the **glance-paced sibling** of [scan-to-action](/work/scan-to-action). Same instrument pattern (*capture → reconcile → directive → log*), different rhythm of human attention. Where scan-to-action runs in seconds-to-minutes during install, compass runs in milliseconds-to-seconds — the time window of a glance.

It's also the first project in the portfolio that points the instrument inward. Comprehension instead of fabrication. Helping the user *be*, not helping the thing *get built*.

## Architecture (one diagram)

```
                    ┌───────────────────────────┐
                    │   GLASSES (Protocol)      │
                    │  capture · trigger · HUD  │
                    └─────────┬─────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
       [VISUAL]         [VERBAL]         [RETRO]
       camera           mic now          mic buffer
              │               │               │
              ▼               ▼               ▼
       VisionProvider    CoachProvider    CoachProvider
       (Claude Sonnet)   (Claude Sonnet)  (Claude Sonnet)
              │               │               │
              └───────────────┼───────────────┘
                              │
                              ▼
                       MemoryStore (SQLite)
                       events · sessions
                       digests · project mem
```

The hardware is abstracted. Visual mode runs against a mock (laptop webcam + simulated HUD) today; real glasses become one more driver when the device decision is made.

## Status

- **Phase 0** — scaffold + mock visual pipeline running end-to-end ✅
- **Phase 1** — first real hardware driver (used Brilliant Labs Frame, eBay alert active)
- **Phase 2** — verbal + retro modes wired to STT and layered memory
- **Phase 3** — V1 sessions with auto-end heuristics, domain coach personas

Full roadmap and decision log in the [repo](https://github.com/barnes-ngb/compass).

## Why this matters

The frontier of smart-glasses products is dominated by ambient-AI failure modes — devices that listen all day, surface things uninvited, and burn through notification budgets in a week. Compass is built on the opposite premise: **pull-default, persistent memory, button-gated retrospection, no continuous recording**. The user controls when compass speaks. The interaction is the glance.

The Zahner-adjacent applications (patina QA, anchor verification, drawing reference) wire compass directly into the rest of the portfolio family — same instrument vocabulary, same mock-first rigor, pointed at a different problem class.

## Tech notes

- Python 3.11/3.12, Windows-first
- `typing.Protocol` for hardware and provider abstractions (no `abc.ABC` ceremony)
- Claude Sonnet 4.6 as the default VLM (best closed-source on the [arXiv CAD-feature recognition benchmark](https://arxiv.org/abs/2411.02810))
- SQLite for layered memory — no server, no ops, easy backup
- `faster-whisper` (local Whisper, `base.en`) for STT — cloud fallback for latency-sensitive cases
- No Docker, no admin rights, runs in a per-user venv

---

[**Repo →**](https://github.com/barnes-ngb/compass) · [**Roadmap →**](https://github.com/barnes-ngb/compass/blob/main/docs/roadmap.md) · [**Decisions →**](https://github.com/barnes-ngb/compass/tree/main/docs/decisions)
