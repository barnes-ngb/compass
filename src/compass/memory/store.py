"""SQLite-backed memory store for compass.

The layered memory pipeline (see docs/decisions/0006-memory-layers.md):

    Live audio  →  Rolling buffer (RAM, never persisted, 30 min default)
                       ↓ on button-press OR session-end
                Session transcript (full STT, persisted)
                       ↓ summarized after session
                Session summary (key points, decisions, open questions)
                       ↓ rolled up daily
                Daily digest (themes, commitments, references)
                       ↓ rolled up over time
                Project memory (recurring threads, your stated goals)

Phase 0 implemented the lowest persistence layer: per-event log. Phase 1b
wires the session layer (run-as-session: one program run is one session,
summarized on exit). The daily digest rollup is Phase 1c. Embeddings and
project memory are Phase 3.

Design choices:
  - SQLite, single file at MEMORY_DB. No server, no ops. Easy backup.
  - Schema is additive — new tables added with `CREATE TABLE IF NOT EXISTS`.
  - No vector embeddings yet. Keyword + recency is enough for V0; we'll add
    embeddings (sqlite-vec or chromadb) when retrieval quality demands it.
  - Raw audio is NEVER stored. Only transcripts. Audio bytes flow from
    rolling buffer → STT → text → here, then audio is discarded.
"""

from __future__ import annotations

import sqlite3
import time
from contextlib import closing
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          REAL    NOT NULL,
    mode        TEXT    NOT NULL,           -- visual | verbal | retro
    query       TEXT    NOT NULL,
    response    TEXT    NOT NULL,
    duration_s  REAL,
    session_id  INTEGER,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_events_ts   ON events(ts);
CREATE INDEX IF NOT EXISTS idx_events_mode ON events(mode);

CREATE TABLE IF NOT EXISTS sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_ts  REAL    NOT NULL,
    ended_ts    REAL,
    label       TEXT,
    transcript  TEXT,
    summary     TEXT
);

CREATE INDEX IF NOT EXISTS idx_sessions_started ON sessions(started_ts);

CREATE TABLE IF NOT EXISTS daily_digests (
    day_iso     TEXT PRIMARY KEY,           -- e.g. '2026-05-20'
    digest      TEXT NOT NULL,
    created_ts  REAL NOT NULL
);
"""


class MemoryStore:
    """Thin SQLite wrapper. Open the connection lazily; close per-call to
    avoid long-lived locks (single user, low write volume — no perf issue)."""

    def __init__(self, db_path: str) -> None:
        self._path = Path(db_path).expanduser().resolve()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self) -> None:
        with closing(sqlite3.connect(self._path)) as conn:
            conn.executescript(SCHEMA)
            conn.commit()

    # ---- events ------------------------------------------------------------

    def log_event(
        self,
        mode: str,
        query: str,
        response: str,
        duration_s: float | None = None,
        session_id: int | None = None,
    ) -> int:
        with closing(sqlite3.connect(self._path)) as conn:
            cur = conn.execute(
                "INSERT INTO events (ts, mode, query, response, duration_s, session_id) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (time.time(), mode, query, response, duration_s, session_id),
            )
            conn.commit()
            return int(cur.lastrowid or 0)

    def recent_events(self, limit: int = 20) -> list[dict]:
        with closing(sqlite3.connect(self._path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM events ORDER BY ts DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    # ---- sessions (Phase 1b — V0 run-as-session) ---------------------------

    def start_session(self, label: str = "") -> int:
        with closing(sqlite3.connect(self._path)) as conn:
            cur = conn.execute(
                "INSERT INTO sessions (started_ts, label) VALUES (?, ?)",
                (time.time(), label),
            )
            conn.commit()
            return int(cur.lastrowid or 0)

    def end_session(
        self,
        session_id: int,
        transcript: str = "",
        summary: str = "",
    ) -> None:
        with closing(sqlite3.connect(self._path)) as conn:
            conn.execute(
                "UPDATE sessions SET ended_ts = ?, transcript = ?, summary = ? "
                "WHERE id = ?",
                (time.time(), transcript, summary, session_id),
            )
            conn.commit()

    def events_for_session(self, session_id: int) -> list[dict]:
        with closing(sqlite3.connect(self._path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM events WHERE session_id = ? ORDER BY ts ASC",
                (session_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_session(self, session_id: int) -> dict | None:
        with closing(sqlite3.connect(self._path)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            return dict(row) if row else None
