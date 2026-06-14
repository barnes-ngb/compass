"""Daily digest rollup. A batch job, separate from the interactive run CLI.

Reads a day's session summaries and rolls them into one daily digest via the
coach, stored in `daily_digests`. Run nightly (Windows Task Scheduler) or
ad-hoc:

    python -m compass.digest                 # today
    python -m compass.digest --date 2026-06-12

Builds only a coach and the memory store. No glasses, no audio, no pipeline.
"""

from __future__ import annotations

import argparse
from datetime import date

from compass.coach.base import CoachProvider
from compass.config import Config, load_config
from compass.memory.store import MemoryStore


def build_digest(
    memory: MemoryStore, coach: CoachProvider, day_iso: str
) -> str | None:
    """Roll the day's session summaries into one digest.

    Returns the digest text, or None if the day has no summarized sessions.
    Re-running overwrites the day's digest (idempotent nightly re-roll).
    """
    sessions = memory.sessions_for_day(day_iso)
    summaries = [s["summary"] for s in sessions if s.get("summary")]
    if not summaries:
        return None
    combined = "\n".join(f"- {s}" for s in summaries)
    digest = coach.respond("summarize the day across these sessions", combined, "")
    if digest:
        memory.upsert_digest(day_iso, digest)
    return digest


def _build_coach(cfg: Config) -> CoachProvider:
    if cfg.coach_provider == "mock":
        from compass.coach.mock import MockCoach
        return MockCoach()
    if cfg.coach_provider == "claude":
        from compass.coach.claude import ClaudeCoach
        return ClaudeCoach(api_key=cfg.anthropic_api_key or "", model=cfg.coach_model)
    raise SystemExit(f"Unknown COACH_PROVIDER={cfg.coach_provider!r}.")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="compass.digest",
        description="Roll up a day's sessions into a daily digest.",
    )
    parser.add_argument(
        "--date", default=None, help="Day to roll up, YYYY-MM-DD. Default: today."
    )
    args = parser.parse_args()
    day_iso = args.date or date.today().isoformat()

    cfg = load_config()
    memory = MemoryStore(cfg.memory_db)
    coach = _build_coach(cfg)

    digest = build_digest(memory, coach, day_iso)
    if digest is None:
        print(f"[compass.digest] {day_iso}: no summarized sessions, nothing to roll up.")
    else:
        print(f"[compass.digest] {day_iso}: digest written ({len(digest)} chars).")


if __name__ == "__main__":
    main()
