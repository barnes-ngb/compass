# 0003 — Claude Sonnet 4.6 as the default VLM provider

**Status:** Accepted · **Date:** 2026-05-19

## Context

Compass needs a vision-language model behind the `VisionProvider` interface for the visual mode (capture → describe → HUD) and behind `CoachProvider` for verbal/retro modes (text → directive). Three viable options in May 2026: Anthropic Claude (Opus 4.7 / Sonnet 4.6 / Haiku 4.5), Google Gemini 2.5 Pro / Flash, OpenAI GPT-5.

The selection criteria for compass specifically:
1. **Accuracy on manufacturing/CAD-style queries** — compass exists in part to serve Zahner-adjacent shop and install use cases.
2. **Latency budget** — total interaction must fit in the "glance" window (≤ 3 s on real hardware).
3. **Cost** — heavy iteration during development; cost-per-query matters.
4. **Python SDK quality** — Windows + PowerShell + no Docker; the SDK has to install and authenticate cleanly.

## Decision

**Default: Claude Sonnet 4.6** (model string `claude-sonnet-4-6`), env-configurable via `VISION_MODEL` and `COACH_MODEL`.

**Drop-in alternatives** wired through the same `VisionProvider` and `CoachProvider` protocols: Haiku 4.5 (cost-sensitive), Opus 4.7 (highest quality for hard prompts), and Gemini 2.5 Flash (vendor diversity, multimodal cost leadership).

## Why Sonnet 4.6 specifically

- **Documented strength on CAD-feature recognition.** The arXiv paper *"Leveraging Vision-Language Models for Manufacturing Feature Recognition in CAD Designs"* (2411.02810, Nov 2024) found Claude 3.5 Sonnet led closed-source models on feature-quantity accuracy (74%), name-matching accuracy (75%), and MAE (3.2). Sonnet 4.6 builds on that lineage; expect parity-or-better.
- **Latency profile.** Sonnet sits in the ~800–1500 ms inference window for a single-image multimodal prompt — fits the 1.5–2.5 s end-to-end budget on a desktop, ~3 s budget on Frame BLE.
- **SDK ergonomics on Windows.** `pip install anthropic` is a single dependency, no native compilation, no Docker. Works in a per-user venv with no admin rights.
- **One Anthropic API key drives both providers.** Vision and coach share auth, billing, and rate-limit context.

## Consequences

**Good:**
- Default works out of the box: install requirements, paste key, run.
- Single vendor for V0 reduces accidental complexity.
- Switching to Haiku for cost or Opus for quality is a one-line env change.

**Bad:**
- Vendor concentration: an Anthropic outage takes compass offline. Mitigation: `MockVision` and `MockCoach` always available; Gemini stub already in `vision/gemini.py` ready to wire when needed.
- Cloud-only. No air-gapped deployment today. Acceptable for office/garage use cases; revisit if the project ever moves toward field-only.

## Alternatives considered

- **Open-source on-device VLM (Moondream 2, Qwen2.5-VL-3B).** Rejected for V0. CAD/manufacturing accuracy lags by 30+ points on the benchmark above. Will revisit when a 7B-class model fits on phone-grade NPUs at acceptable accuracy.
- **GPT-5 / GPT-5 mini.** Strong but adds a second vendor for marginal gain. Already a stub in `vision/`; trivial to wire if Sonnet falters.
- **Gemini 2.5 Pro as default.** Strong multimodal model and a reasonable second choice; Sonnet 4.6 wins on the CAD-feature evidence above.
