# Inspection report — directive-engine and scan-to-action

Date: 2026-05-20
Scope: read-only audit of two sibling repos referenced by `docs/portfolio-fit.md`.
Method: cloned both repos locally, read READMEs, grepped source, inspected schemas and a fixture dataset. Did not run tests (no `node_modules` available in inspection env).

---

## directive-engine

### Status check

- Last commit: `2026-05-15` — "Merge PR #143: README v0.2 — lead with demo and write-up." Active in the last week.
- File count: ~163 tracked files; `src/` is ~11.9k lines of TypeScript across ~85 `.ts` files (`find src -name "*.ts" -exec wc -l`).
- Languages: TypeScript (engine, viewer, CLI). No Python.
- Entry points that work today:
  - CLI: `src/cli/index.ts` — `tsx src/cli/index.ts --nominal … --asbuilt … --constraints … --out out/directives.json` (package script `npm run gen`).
  - Browser demo: `vite` dev server, deployed at `directive-engine.vercel.app` (per README).
  - Point-cloud ingest script: `npx tsx scripts/ingest-pointcloud.ts <scan.ply> <part-lines.json>`.
- Tests: 23 test files under `src/__tests__/` and `src/presentation/`, `src/viewer/`. Grep finds ~185 `it()`/`test()` cases (README claims "187 unit tests passing" — close enough that the claim is plausible; not run in this audit because `node_modules` is not installed).
- Recent dev activity: heavy. PRs up to #143, multiple "Phase N" merges (Phase 6c, 9, 12), v0.2 README cleanup, MIT license added 2026-05-12, point-cloud ingest landed shortly before.

### What it actually does (vs. what its README claims)

The engine takes three JSON inputs — **nominal part poses**, **as-built part poses**, and **per-part constraints** (allowed DOF, tolerances, clamp limits, optional indexed-rotation table) — and emits a **directives JSON** that lists, per part, a status (`ok | pending | clamped | blocked | needs_review`), the computed pose deviation, and a sequence of installer actions (`translate`, `rotate`, `rotate_to_index`, `noop`) plus a verification block. The README's "as-built reality → installer-ready directives" framing matches the code.

The v0.2.1 point-cloud ingest layer (`src/pipelines/pointcloudIngest.ts`) turns ASCII PLY/XYZ + nominal part lines into an `AsBuiltPosesDataset` via anchors → Horn's-method rigid alignment → tube segmentation → PCA line fit → pose + confidence. Tested in `src/__tests__/pointcloud.ingest.test.ts`. README is honest about scope cuts: pose recovery returns identity rotation, one line per part, ASCII-only.

**Core (load-bearing):** `generateDirectives` at `src/core/generateDirectives.ts:511` (670 lines), plus `src/core/math/`, `src/core/align/`, `src/core/scan/`.
**Scaffolding:** `src/viewer/` (28 files, three.js demo, cleanly separated via `engine-bridge.ts`), `src/presentation/format-directive.ts`, `src/cli/`, `schemas/`, `datasets/`.

### Architecture sketch

| Module | Role |
|---|---|
| `src/core/generateDirectives.ts` | Main pipeline: compute deviation → check tolerance/confidence/limits → emit per-part actions + verification |
| `src/core/types.ts` | All input/output dataclasses (`NominalPosesDataset`, `AsBuiltPosesDataset`, `ConstraintsDataset`, `DirectivesOutput`, `Step`, `Action`) |
| `src/core/align/`, `src/core/math/` | Rigid-transform math, quaternion ops, per-axis clamping |
| `src/core/scan/` | PCA line fit, segmentation, pose-from-fit with confidence scoring |
| `src/pipelines/pointcloudIngest.ts` | ASCII PLY/XYZ → `ScanPoint[]` → `AsBuiltPosesDataset` |
| `src/cli/index.ts` | Thin file-IO wrapper around `generateDirectives` |
| `src/presentation/format-directive.ts` | Renders a `Step` into installer-language English using optional named `Feature`s (slots, joints, indexed bolt patterns) |
| `src/viewer/` | Browser 3D demo (three.js); 28 files |
| `schemas/` | JSON Schemas for every input and output |

**Inputs:** three JSON files (mm; quaternion `[x,y,z,w]`; `frame_id = "world"`). Schemas at `schemas/{as_built,constraints,pose_nominal,pose_asbuilt}.schema.json`.
**Output:** JSON matching `schemas/directives_output.schema.json`. Note: the fixture at `datasets/toy_facade_v1/expected_directives.json` uses an older shape (`computedDeviationMm`, `priority`) while `src/core/types.ts:204` emits `computed_errors.{translation_error_mm_vec, translation_error_norm_mm, rotation_error_deg}` and `reason_codes[]`. Schema and code agree; fixture lags.

**External deps:** `three` (viewer only), `qrcode`. No CAD format, no proprietary scanner SDK. PLY parser is hand-rolled.

### Deviation vs. directive content

- **Deviation logic** lives inline in `generateDirectives.ts` as `computeErrors(nominal, asBuilt)`, emerging as the `computed_errors` field on every `Step` (`src/core/types.ts:198`). Its math primitives (`sub`, `norm`, `deltaQuat`, `toAxisAngle`, `clampQuatAngle`) are in `src/core/math/{vec,quat}.ts` and already stand alone.
- **Directive logic** is the rest of `generateDirectives.ts` — the per-part state machine that turns errors + constraints into `{status, reason_codes, actions, verification}`. A directive at runtime is a `Step` (`src/core/types.ts:204`); fixture sample at `datasets/toy_facade_v1/expected_directives.json:23`:

  ```json
  { "stepId": "S-0004", "partId": "P-04", "status": "pending",
    "computedDeviationMm": 3.5,
    "actions": [{ "type": "translate", "frame": "part",
                  "vectorMm": [-3.5, 0, 0], "clampApplied": false }],
    "verification": { "type": "measure_pose", "passIfMaxDeviationMm": 2 } }
  ```
- **Smallest clean cut** to extract deviation: move `computeErrors` + `ComputedErrorsInternal` from `generateDirectives.ts` into a new `src/core/deviation.ts` (it would re-export `src/core/math/` and `src/core/align/apply.ts`, which are already standalone). `generateDirectives` becomes a pure consumer of `{nominal, asBuilt} → ComputedErrors` then `{errors, constraints} → Step`. ~50 lines moved; low-risk.

### How compass could realistically consume this

- Callable today: the CLI (`tsx src/cli/index.ts …`) reads three JSON files and writes one — the stable seam. JSON Schema for output is published at `schemas/directives_output.schema.json`.
- Compass is Python; directive-engine is TypeScript-only. No Python binding, no HTTP server, no in-process import path.
- Practical options, by effort: (1) shell out to the CLI (compass writes JSON inputs, runs `npx tsx`, parses JSON output — requires Node + a directive-engine checkout); (2) consume directives produced offline as static JSON; (3) adopt the JSON Schema as an upstream contract and only render, not compute.
- **Realism:** wiring compass to directive-engine **today** is *premature*, not blocked. Schema and CLI exist; integration is ~half a day. But compass's Visual mode doesn't need a directive yet — it needs a `whatami` answer from a VLM. Wire when a Phase-1 demo concretely asks for a per-anchor directive on the HUD.

---

## scan-to-action

### Status check

- Last commit: `2026-05-12` — Merge PR #1, "add MIT license."
- 2 files: `LICENSE`, `README.md`. No `src/`, no tests, no `package.json` or `pyproject.toml`. No code, no entry points, no tests. One commit of substance.

### What it actually does (vs. what its README claims)

The entire README is one line: `align wall/global frame → detect/solve anchor pose → compute per-part delta with constrained DOF`. There is no implementation. Notably, that one-line description **already describes what directive-engine does** (Horn's rigid alignment, per-part pose-delta under DOF constraints).

### Architecture sketch

| Module | Role |
|---|---|
| `README.md` | One-sentence intent statement |
| `LICENSE` | MIT |

Inputs: none. Outputs: none. Dependencies: none.

### Deviation vs. directive content

- Working code? **No.** Stub — name and license only.
- Original intent (inferred from README): a scan-side pipeline aligning a captured scan to a global frame, solving anchor pose, then emitting per-part deltas under DOF constraints. This overlaps substantially with directive-engine's `src/core/align/rigid.ts` + `src/core/scan/` + `src/core/generateDirectives.ts`. **Unknown** whether scan-to-action was meant as a Python port, a scan-time service feeding directive-engine, or has been superseded by directive-engine's v0.2 ingest — would need to ask Nathan.
- **Stub. No code exists in this repo as of 2026-05-20.**

### How compass could realistically consume this

- Nothing to consume. No API, no CLI, no schema, no file format.
- To be consumable, scan-to-action would need (a) an implementation, (b) an input format (scan + nominal layout), (c) an output format (ideally compatible with directive-engine's `DirectivesOutput`), and (d) a CLI or service. None exist.
- **Realism:** **blocked** — nothing on the other side of the wire.

---

## Recommendations for compass's portfolio-fit doc

1. **directive-engine is the real sibling.** Only one of the two with an implementation, tests, schemas, a CLI, a deployed browser demo, and active development. Any compass reference to "the directive engine that computes per-anchor moves" should point at directive-engine, not scan-to-action.
2. **scan-to-action: mark aspirational or omit.** It is a name + license + one-line README. Listing it as a peer in the instrument table is misleading. Either tag it "placeholder, not yet implemented" or drop the row until it has working code.
3. **"Deviation logic extraction" is a future option, not the current state.** Deviation math is inlined into `generateDirectives.ts` today. A ~50-line refactor would extract it cleanly (see above). Worth recording if compass — or a future scan-to-action — wants deviation math without the whole engine. Do not claim it's already factored.
4. **Invalidated claim:** `docs/portfolio-fit.md`'s row attributing "laser scan of installed substrate → compare to BIM anchor layout under DOF constraints → move-anchor directive" to scan-to-action describes capabilities that **live in directive-engine**. The portfolio-fit table needs to either merge those rows or clearly mark scan-to-action as not-yet-built.
5. **Invalidated framing:** the "compass ↔ scan-to-action" section assumes a "scan-to-action API for that anchor's directive." No such API exists. A realistic Phase-1 directive-on-HUD demo should target directive-engine's CLI/JSON output, not a scan-to-action endpoint.
