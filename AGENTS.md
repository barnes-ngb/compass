# AGENTS.md

Conventions for agents (Claude Code, future Claude conversations, anything automated) working on this repo. If you're a human contributor, see `README.md` and `docs/`.

## Operating principles

- **One task per PR.** Do not combine unrelated work, however small. Easier to review, easier to roll back.
- **Branch name is provided.** Prompts include an explicit `claude/<short-description>` branch name. Use it. (The session harness may append a random suffix — that's fine.)
- **Commit message is provided.** Prompts include the exact commit message to use. Do not improvise.
- **Surface, don't fix.** If you notice something broken or stale outside the scope of the prompt, list it in the PR body under "Noticed but not changed." Do not change it in this PR.
- **Cite paths.** When making a claim about the code, reference the file and line. E.g., "the protocol at `src/compass/glasses/base.py:23`."
- **Verify, don't trust.** Run `pytest` and report results in the PR body. Do not assume tests pass.
- **Constraints are hard.** "Do NOT modify X" means do not modify X, even if you have a good reason. If you find a real conflict between the prompt and reality, stop and surface it; don't work around.

## Project conventions

- **Mock-first.** Every Protocol gets a mock implementation. See ADR 0001 (`docs/decisions/0001-mock-first.md`).
- **Protocols, not ABCs.** Hardware and provider abstractions use `typing.Protocol` with `@runtime_checkable`. See ADR 0002.
- **`src/` layout.** Source lives in `src/compass/`; tests in `tests/`. The `compass` package is installed editable via `pip install -e .`.
- **Three coach modes.** Visual / Verbal / Retro share one backend. See ADR 0005.
- **Layered memory.** Rolling buffer → session → daily digest → project. Raw audio bytes are NEVER persisted. See ADR 0006.
- **Windows-first dev environment.** PowerShell, no Docker, no admin rights, `py -3` to launch.

## PR body template

Every PR should include:

1. A 1–3 sentence summary of *why* the change exists.
2. The exact list of files modified.
3. Verification — at minimum, `pytest` output. For protocol or interface changes, also note that imports still resolve.
4. "Noticed but not changed" — things you saw that are out of scope.
5. (If a verification-only PR with no code changes) An "Open questions for Nathan" section.

## Reading order for a fresh agent

If you're picking up this repo cold, read in this order:

1. `README.md` — what compass is and how to run it
2. `docs/architecture.md` — modules and their responsibilities
3. `docs/decisions/0005-coach-modes.md` — the three-mode model
4. `docs/decisions/0006-memory-layers.md` — the memory pipeline
5. `docs/roadmap.md` — what's done, what's next
6. `docs/portfolio-fit.md` — how compass sits alongside directive-engine and scan-to-action
7. This file

For audits or framing claims about sibling repos, `docs/inspection/` is the source of truth.

## What's out of scope for agents

- **Don't pre-buy hardware decisions.** Hardware acquisition is a human decision (see `docs/decisions/0004-hardware-strategy.md`). Don't add `frame-msg` or `vuzix-sdk` or anything similar to dependencies without an explicit prompt.
- **Don't add cloud sync.** Memory is local SQLite by design (ADR 0006). Don't add Postgres, Firebase, or any sync layer without an explicit prompt.
- **Don't add continuous recording.** The rolling buffer is RAM-only by architectural commitment (ADR 0006). Don't add disk persistence of raw audio.
- **Don't add ambient AI features.** Pull-default is the design (ADR 0005). Don't add wake-word listening, always-on transcription, or notification surfaces without an explicit prompt.

## Updating this file

Update `AGENTS.md` when:
- A new convention emerges across 2+ PRs and would be worth codifying.
- A previous convention turns out to be wrong (rare; flag in the PR body).
- A new ADR adds an architectural constraint relevant to agents.

Do NOT update `AGENTS.md` opportunistically during an unrelated PR.
