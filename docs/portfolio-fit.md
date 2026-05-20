# compass — Portfolio Fit

How compass sits alongside the rest of the work.

---

## The instrument pattern

Every project in the portfolio is some variant of the same shape:

> **scan → reconcile → directives → build**

Pull something messy out of the real world. Compare it to a digital target. Compute the next action. Hand a person (or a machine) instructions specific to *this* gap.

| Project | Scan | Reconcile | Directive | Build |
|---|---|---|---|---|
| **scan-to-action** | Laser scan of installed substrate | Compare to BIM anchor layout under DOF constraints | "Move anchor 14 down-and-left 3.2 mm" | Installer adjusts before panel hangs |
| **directive-engine** | Spec drawings + tolerances | Compare panel-as-fabricated to drawing | Cut/bend/finish sequence | CNC + shop floor |
| **patina-model** | Initial finish state + environmental input | Compare predicted vs. observed patina evolution | "Move panel 7 to controlled-humidity bay" | Patina aging program |
| **induction-patina** | Real-time IR + induction control | Compare patina-model target to current state | Adjust induction power/duty | In-situ patina control |
| **compass** | Live camera frame, voice query, or audio-buffer transcript | Compare to user's stated goals, project memory, drawings, prior decisions | Glanceable HUD answer | User's next move (knowing, deciding, asking) |

Compass is the **glance-paced** sibling: same instrument, different rhythm of human attention. Where scan-to-action runs in seconds-to-minutes (installer waits for the directive before moving), compass runs in *milliseconds-to-seconds* — the time window of a glance.

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

These are not aspirational. They're real wire-in points the architecture supports.

### compass ↔ scan-to-action

The Visual mode is a thin field-side client for scan-to-action's directives. The scan-to-action engine computes "move anchor 14 down-and-left 3.2 mm" in the office. Compass *shows it on the installer's HUD in the field*. The reconciliation happens server-side; compass is the last 18 inches.

Phase 1 demo idea: hold a phone showing a fiducial-marked anchor → compass reads the fiducial, queries the scan-to-action API for that anchor's directive, shows on HUD.

### compass ↔ patina-model

The Visual mode + the patina-model + Sonnet 4.6 = a patina QA station. Photo the current panel state → ship to a cloud worker that pulls the patina-model's predicted T+90-day state for that panel → VLM compares observed vs. predicted → HUD answer: "matches predicted ±10%" or "30 days early in oxidation."

Phase 2/3 demo idea: this is the single most-Zahner application in the family. No competitor has the predictive thermodynamics + the field instrument together.

### compass ↔ directive-engine

The Retro mode is the directive-engine's feedback channel. Field-as-built notes from compass sessions feed back into directive-engine's tolerance models. "What did we end up doing about that 16-ga substitution last Tuesday?" — compass remembers, directive-engine learns.

### compass ↔ induction-patina

Out of scope short-term. But the same `Glasses` Protocol could front-end an induction-patina control system: HUD shows current coil power + target state, voice updates target. Phase 4+.

---

## Where compass doesn't fit, on purpose

- Compass is not AR. No marker tracking, no registered overlays, no 6DoF. That's [scan-to-action]'s problem (and a hard one). Compass is glanceable text in your right eye, not a hologram.
- Compass is not a safety-critical system. It runs in office and garage contexts. Not on a casthouse floor, not in PPE-required environments. RealWear Navigator 520 is the answer for those; we'd be a partner, not a replacement.
- Compass is not a meeting-bot. It doesn't transcribe meetings the user isn't in, doesn't surveil others, doesn't continuously record. See `docs/decisions/0006-memory-layers.md`.

---

## Portfolio page positioning

On the barnes-portfolio-site, compass lands as:

- A **sibling card** next to scan-to-action, patina-model, directive-engine — same visual family, same instrument vocabulary.
- An entry whose first sentence is the thesis: *"Understand my world better, don't miss things, get insight from the wealth of knowledge plus me."*
- A demo video showing the laptop mock (Phase 0) → real Frame (Phase 1) progression.
- Honest about hardware status — links to `docs/landscape.md`, doesn't pretend Halo is shipping when it isn't.

Draft page lives at `web/compass.md`, ready to drop into the Astro site at `src/pages/work/compass.md`.

---

## What compass is *for*, in one sentence

It's a small, pull-default, glance-paced AI coach that helps you understand your world better — with the same instrument-design rigor as the fabrication-side projects, pointed at a different problem.
