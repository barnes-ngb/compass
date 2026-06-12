# 0008 — Hardware path: Halo primary, Frame backup, no committed fallback

**Status:** Accepted · **Date:** 2026-05-20 · **Supersedes (for current decision):** 0004

## Context

ADR 0004 framed used Frame on eBay as the Phase 1 primary, with Halo and Meta Display as watch list. Since then:

- Project scope expanded to three modes (Visual / Verbal / Retro) per ADR 0005. Phase 2 modes can be built on the laptop mock without any glasses; only Phase 1 (a real `Glasses` driver) is hardware-gated.
- Halo was ordered on 2026-05-20 (Brilliant Labs order #912503, Black, $349 + $39 shipping). Ship date undefined as of order time.
- eBay alert for used Frame remains active.
- Halo's SDK is still a stub at `docs.brilliant.xyz/halo/halo/`. The expectation is the SDK ships with or shortly after the device.

## Decision

- **Primary Phase 1 device:** Brilliant Labs Halo (ordered).
- **Backup acquisition:** used Frame H20 on eBay if one appears at $135–200 before Halo ships. If acquired, becomes a secondary `Glasses` driver alongside Halo — neither replaces the other.
- **No committed fallback trigger.** We deliberately do not pre-commit to "if Halo slips past date X, buy Z100+Mentra." Reasons:
  - Phase 2 work proceeds independently on the laptop mock; we're not blocked on hardware while waiting.
  - The architecture's `Glasses` Protocol means switching devices is bounded work, not a rewrite.
  - Committing to a fallback now means making a decision before we have new information. Better to re-evaluate when there's a reason to.

## What would trigger re-evaluation

Not a commitment, just a list of plausible signals:

- Brilliant Labs announces another slip past Q4 2026.
- Phase 2 retro mode is fully wired on the laptop mock and we want to demo on real hardware before Halo arrives.
- A used Frame appears on eBay at a price worth grabbing.
- The Halo SDK page (`docs.brilliant.xyz/halo/halo/`) updates with concrete API surface, raising or lowering confidence in the SDK story.
- Meta Connect 2026 (Sept 23–24, 2026) produces Ray-Ban Display GA news that changes the calculus.

When any of these fires, this ADR gets a postscript or a successor ADR — not a silent change.

## Consequences

**Good:**

- Single primary device choice, single backup, no analysis paralysis.
- Phase 2 work unblocked entirely.
- Halo's portfolio narrative (color HUD, on-device NPU, privacy-first) is the strongest of any current option *if* it ships well.
- The `Glasses` Protocol means the cost of being wrong is bounded.

**Bad:**

- We're betting on Brilliant Labs' execution. They've slipped twice already.
- No SDK on the day Halo arrives means a Phase 1 hardware driver may not be writable immediately even after hardware lands.
- "No fallback trigger" requires us to actually re-evaluate when conditions change rather than letting a calendar-based fallback fire automatically.

## Watching

- Brilliant Labs order page (weekly) for ship updates.
- `docs.brilliant.xyz/halo/halo/` (monthly) for SDK readiness.
- eBay saved search for "Brilliant Labs Frame" (passive — pushes notify).
- `docs/landscape.md` quarterly re-check.

## Alternatives considered

- **Commit to a calendar-based fallback (e.g., "Z100+Mentra if Halo not shipping by Aug 19, 2026").** Rejected: the trigger date is arbitrary, and committing now means making a decision without information we'd have later.
- **Buy Z100+Mentra now in parallel.** Rejected: $800 of hardware sitting on a desk before we've maxed out the mock is premature. The architecture survives the wait.
- **Wait for Halo without ordering.** Rejected: ordered already; this ADR ratifies the decision.
- **Pure used-Frame strategy.** Still active as the backup path. Not chosen as primary because Halo's portfolio narrative is stronger if it ships.

## Cross-references

- ADR 0001 (Mock-first) — why we can wait on hardware
- ADR 0002 (Glasses as Protocol) — why hardware swaps are bounded
- ADR 0004 (Original hardware strategy) — superseded for current decision; preserved as historical context
- ADR 0005 (Coach modes) — what hardware needs to support
- `docs/landscape.md` — full landscape survey
- `docs/inspection/2026-05-20-sibling-repos.md` — directive-engine as the consumption target

## Postscript: 2026-06-12 — Halo SDK published and PCBs in production

Two material updates since this ADR was written:

1. Brilliant Labs published the Halo SDK at https://docs.brilliant.xyz/halo/halo-sdk/ (was previously a stub). A `brilliant-msg` Python package (BSD license, Windows-supported, Python 3.10+) is on PyPI; example code is in https://github.com/brilliantlabsAR/brilliant_sdk. SDK evaluation: see the deep-research artifact in the project context.
2. Brilliant notified pre-order #912503 on 2026-06-12 that PCBs are made. Foxconn QA the week of 2026-06-15; production kick-off the week of June 21 or 28. Realistic delivery still trends late Q3 / Q4 2026 (PCB-ready to customer delivery historically takes Brilliant 2–4 months), but the schedule is no longer hypothetical.

Decision unchanged: Halo remains primary, Frame remains the backup acquisition. ADR 0009 documents the *implementation strategy* (Python host + minimal Lua + phone deferred) now that the SDK is concrete enough to commit to.
