# compass — Portfolio Fit

How compass sits alongside the rest of the work.

---

## The instrument pattern

Every project in the portfolio is some variant of the same shape:

> **scan → reconcile → directives → build**

Pull something messy out of the real world. Compare it to a digital target. Compute the next action. Hand a person (or a machine) instructions specific to *this* gap.

| Project | Status | Scan | Reconcile | Directive | Build |
|---|---|---|---|---|---|
| **scan-to-action** | stub (placeholder; intent only) | *(intended)* Laser/point-cloud scan of installed substrate, aligned to a global frame | *(intended)* Solve anchor pose, compute per-part delta under DOF constraints — a scan-side ingest layer feeding a downstream directive engine | *(intended)* Hand off per-anchor deviations | *(intended)* Downstream consumer (today, directive-engine) emits the installer move |
| **directive-engine** | built | Ingests nominal-pose + as-built-pose + per-part constraints JSON (and, since v0.2.1, ASCII PLY/XYZ point clouds via `src/pipelines/pointcloudIngest.ts`) | Horn's-method rigid alignment, per-anchor deviation math (`computeErrors` inside `src/core/generateDirectives.ts`), per-axis DOF clamping | Emits a per-part `Step` with `status` (`ok \| pending \| clamped \| blocked \| needs_review`), `actions` (`translate`, `rotate`, `rotate_to_index`, `noop`), and a `verification` block — JSON matching `schemas/directives_output.schema.json` | CLI (`tsx src/cli/index.ts …`) writes the directives JSON; installer / CNC / shop floor consumes it |
| **patina-model** | (out of scope for this audit) | Initial finish state + environmental input | Compare predicted vs. observed patina evolution | "Move panel 7 to controlled-humidity bay" | Patina aging program |
| **induction-patina** | (out of scope for this audit) | Real-time IR + induction control | Compare patina-model target to current state | Adjust induction power/duty | In-situ patina control |
| **compass** | built (Phase 0) | Live camera frame, voice query, or audio-buffer transcript | Compare to user's stated goals, project memory, drawings, prior decisions | Glanceable HUD answer | User's next move (knowing, deciding, asking) |

Compass is the **glance-paced** sibling: same instrument, different rhythm of human attention. Where the fabrication-side instruments run in seconds-to-minutes (installer waits for the directive before moving), compass runs in *milliseconds-to-seconds* — the time window of a glance.

### Where the implementations actually live

Today, **directive-engine spans both the scan and directive layers of the pattern.** Its `src/core/generateDirectives.ts` houses the rigid alignment + per-anchor deviation math *and* the per-part state machine that turns those errors into installer-ready directives (per `docs/inspection/2026-05-20-sibling-repos.md` § directive-engine § Deviation vs. directive content). The ingest of raw point-cloud scans into as-built poses also lives in directive-engine (`src/pipelines/pointcloudIngest.ts`, per the inspection's § directive-engine § What it actually does).

**scan-to-action**, by contrast, is a name and a license. The inspection found two files — `LICENSE` + a one-line `README.md` — and no source, tests, schemas, CLI, or entry points (per `docs/inspection/2026-05-20-sibling-repos.md` § scan-to-action § Status check). The one-line README's intent (*"align wall/global frame → detect/solve anchor pose → compute per-part delta with constrained DOF"*) already describes what directive-engine does today.

The deviation math could be cleanly **extracted** — the inspection estimates ~50 lines moved from `generateDirectives.ts` into a new `src/core/deviation.ts`, re-exporting the already-standalone `src/core/math/` and `src/core/align/apply.ts` (per `docs/inspection/2026-05-20-sibling-repos.md` § directive-engine § Deviation vs. directive content). That refactor would populate scan-to-action with real code — turning it from aspirational placeholder into the dedicated scan-side ingest layer the instrument-pattern table imagines. **This is a future option, not a planned PR.**

---

## What's distinctive about compass

The other instruments serve **fabrication and install**. They make physical things easier to get right.

Compass serves **comprehension**. It makes the *user* easier to be — fewer forgotten threads, fewer "what did they just say?" gaps, easier access to expertise mid-task.

It's the first instrument in the family that points inward.

That matters for the portfolio because:
- It demonstrates the instrument pattern generalizes beyond fabrication.
- It shows a willingness to point the same rigor (mock-first, abstracted hardware, layered memory) at a different problem class.
- It's a *visible* product — anyone watching a demo video understands what's happening, unlike (say) anchor alignment under DOF constraints.

---

## Where compass connects to the rest

These are realistic wire-in points. Status (built / feasible / aspirational) is called out for each.

### compass ↔ directive-engine (consumption)

**Status:** feasible, not done. Not blocked.

A realistic wire-in: compass shells out to directive-engine's CLI

```
tsx src/cli/index.ts --nominal X --asbuilt Y --constraints Z --out W
```

parses the resulting directives JSON (schema: `schemas/directives_output.schema.json`), and renders a per-anchor directive on the HUD — `status`, the action vector, and the verification step. directive-engine is TypeScript; compass is Python. **The wire is over a CLI/JSON boundary, not in-process** — compass writes three JSON inputs, runs `npx tsx`, and reads one JSON output (per `docs/inspection/2026-05-20-sibling-repos.md` § directive-engine § How compass could realistically consume this). There is no Python binding and no HTTP API.

The inspection's assessment: *"wiring compass to directive-engine today is premature, not blocked. Schema and CLI exist; integration is ~half a day"* (per `docs/inspection/2026-05-20-sibling-repos.md` § directive-engine § How compass could realistically consume this). It's premature today because compass's Visual mode doesn't yet need a directive — it needs a `whatami` answer from a VLM. Revisit when a Phase-1 demo concretely asks for a per-anchor directive on the HUD.

### compass ↔ patina-model

**Status:** aspirational (no audit on this sibling in this round).

The Visual mode + the patina-model + Sonnet 4.6 = a patina QA station. Photo the current panel state → ship to a cloud worker that pulls the patina-model's predicted T+90-day state for that panel → VLM compares observed vs. predicted → HUD answer: "matches predicted ±10%" or "30 days early in oxidation."

Phase 2/3 demo idea: this is the single most-Zahner application in the family. No competitor has the predictive thermodynamics + the field instrument together.

### compass ↔ directive-engine (feedback)

**Status:** aspirational.

The Retro mode is directive-engine's feedback channel. Field-as-built notes from compass sessions feed back into directive-engine's tolerance models. "What did we end up doing about that 16-ga substitution last Tuesday?" — compass remembers, directive-engine learns. This is the opposite direction of the *consumption* wire above: data flows compass → directive-engine rather than directive-engine → compass.

### compass ↔ induction-patina

**Status:** out of scope short-term.

But the same `Glasses` Protocol could front-end an induction-patina control system: HUD shows current coil power + target state, voice updates target. Phase 4+.

---

## Where compass doesn't fit, on purpose

- Compass is not AR. No marker tracking, no registered overlays, no 6DoF. That's the scan-side problem (and a hard one). Compass is glanceable text in your right eye, not a hologram.
- Compass is not a safety-critical system. It runs in office and garage contexts. Not on a casthouse floor, not in PPE-required environments. RealWear Navigator 520 is the answer for those; we'd be a partner, not a replacement.
- Compass is not a meeting-bot. It doesn't transcribe meetings the user isn't in, doesn't surveil others, doesn't continuously record. See `docs/decisions/0006-memory-layers.md`.

---

## Portfolio page positioning

On the barnes-portfolio-site, compass lands as:

- A **sibling card** next to directive-engine (built), patina-model, and scan-to-action (placeholder) — same visual family, same instrument vocabulary, honest about which siblings are built and which are aspirational.
- An entry whose first sentence is the thesis: *"Understand my world better, don't miss things, get insight from the wealth of knowledge plus me."*
- A demo video showing the laptop mock (Phase 0) → real Frame (Phase 1) progression.
- Honest about hardware status — links to `docs/landscape.md`, doesn't pretend Halo is shipping when it isn't.

Draft page lives at `web/compass.md`, ready to drop into the Astro site at `src/pages/work/compass.md`.

---

## What compass is *for*, in one sentence

It's a small, pull-default, glance-paced AI coach that helps you understand your world better — with the same instrument-design rigor as the fabrication-side projects, pointed at a different problem.

---

## Audit trail

The framing in this document reflects findings from the sibling-repo inspection at [`docs/inspection/2026-05-20-sibling-repos.md`](inspection/2026-05-20-sibling-repos.md) (landed via PR #8). In particular:

- The instrument-table row for **scan-to-action** is downgraded from "built sibling" to "stub (placeholder; intent only)" per § scan-to-action § Status check.
- The capabilities previously attributed to scan-to-action (rigid alignment + per-anchor deviation + directive emission) are reattributed to **directive-engine** per § directive-engine § What it actually does.
- The earlier "compass ↔ scan-to-action" wire-in section is replaced by "compass ↔ directive-engine (consumption)" per § directive-engine § How compass could realistically consume this.
- The "deviation logic extraction" note reflects the inspection's ~50-line refactor estimate, recorded as a future option only.
