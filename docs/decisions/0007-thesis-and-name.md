# 0007 — The thesis and the name

**Status:** Accepted · **Date:** 2026-05-19

## Context

The project's name and thesis sentence shape everything downstream — repo name, docs, voice trigger, portfolio framing, how a reader feels about it in the first ten seconds. Worth being deliberate.

### The naming history

| Name | Why proposed | Why rejected |
|---|---|---|
| `frame-naturalist` | The original sketch — observe naturally, like in a field journal. | Too hardware-coupled (Brilliant Labs Frame). Too narrow (only describes the visual mode). |
| `glance-to-directive` | Sibling to `scan-to-action`. Same instrument pattern, glance-paced. | Captures the visual mode well; doesn't capture the *memory* or *retrospective* dimensions that emerged in design. Also: as a voice trigger or in a chat, the word "directive" is intimidating. |
| `anchor` | Strong portfolio resonance (anchor alignment is the heart of scan-to-action). | Risk of auto-trigger: "anchor" comes up often in shop talk. A voice-activated coach that fires every time someone says "anchor" is broken. |
| `compass` | Universal evocation: orientation, finding your way, helps you not get lost. Two syllables, easy voice trigger. Rare in conversation. | Slight risk of feeling generic — many products are named compass. Mitigated by the specific thesis it points to. |

### The thesis evolution

The original framing — *"capture → reconcile → directive → build"* — describes the *visual* mode well, but it positions compass as a tool for outputting actions. That's incomplete. The lived problem is bigger and quieter than that.

A clearer articulation, in the user's own words during design:

> *"I'm really just trying to understand my world better, not miss out on things that I just forget, but also get insight because I've got this wealth of knowledge and the AI engine."*

That sentence is the thesis. Compress it to:

> *"Understand my world better, don't miss things, get insight from the wealth of knowledge plus me."*

## Decision

**Name: `compass`.**

**Thesis:** "Understand my world better, don't miss things, get insight from the wealth of knowledge plus me."

The name appears in: the repo, the Python package, the voice trigger (`"hey compass"` reserved for verbal mode), the portfolio page, the README. The thesis sentence appears at the top of the README and the portfolio page.

## Consequences

**Good:**
- One-word name. Easy to say, easy to type, easy to remember.
- Voice trigger is two syllables and rare in conversation — low false-positive risk.
- The metaphor is honest. A compass doesn't tell you where to go; it tells you where you are and which direction is which. That matches a pull-default coach: you make the choices, compass keeps you oriented.
- Portfolio-friendly. Compass sits alongside `scan-to-action`, `directive-engine`, `patina-model` as a shop-vocabulary name (orientation instrument) without being literally tied to Zahner work.

**Bad:**
- Many products are named some variant of compass. Worth a trademark sanity check before we publish anything commercial. For a personal portfolio project, the name is fine.
- The metaphor doesn't capture the *memory* dimension directly. A compass tells you direction now; it doesn't remember where you've been. The thesis carries the memory weight; the name carries the orientation weight. That's an acceptable split.

## What this changes downstream

- Repo: `barnes-ngb/compass`
- Python package: `compass` (was `glance_to_directive`)
- Voice trigger (verbal mode, Phase 2): `"hey compass"` or just the button press
- Portfolio page: `web/compass.md` → Astro `src/pages/work/compass.md` on the barnes-portfolio-site
- README tagline updated to thesis sentence
- ADRs `0001` through `0006` already use the name

## Alternatives considered (and why each lost)

- **`throughline`** — captures the memory/retrospective dimension well, but four syllables, hard to voice-trigger, and reads as "obscure literary term" rather than "wearable instrument."
- **`recall`** — describes the Retro mode perfectly but undersells Visual and Verbal.
- **`peripheral`** — clever (lives at the edge of vision and attention) but abstract and forgettable.
- **`Alfred`, `Clippy`, manufactured-letter names like `periX`** — `Alfred` is too borrowed from existing metaphors (every personal-AI is named after a butler or assistant). `Clippy` carries the wrong vibe. Manufactured-letter names read as "trying to be memorable" rather than memorable.
