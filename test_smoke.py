"""Smoke tests for compass.

Run with:
    pytest tests/

These don't need network access — they exercise the abstractions, the
text-wrapping logic, the mock providers, and SQLite memory roundtrip.
Real Claude/Frame integration is tested manually.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from compass.coach.base import CoachProvider
from compass.coach.mock import MockCoach
from compass.glasses.base import Glasses
from compass.memory.store import MemoryStore
from compass.pipeline import _two_lines
from compass.vision.base import VisionProvider
from compass.vision.mock import MockVision


def test_mock_vision_satisfies_protocol() -> None:
    vision = MockVision()
    assert isinstance(vision, VisionProvider)


def test_mock_coach_satisfies_protocol() -> None:
    coach = MockCoach()
    assert isinstance(coach, CoachProvider)


def test_glasses_protocol_is_structural() -> None:
    class FakeGlasses:
        def connect(self) -> None: ...
        def wait_for_trigger(self) -> bool: return False
        def capture_image(self) -> bytes: return b""
        def show_text(self, line1: str, line2: str = "", color: str = "white") -> None: ...
        def close(self) -> None: ...

    assert isinstance(FakeGlasses(), Glasses)


def test_mock_vision_returns_nonempty() -> None:
    v = MockVision()
    assert v.describe(b"\xff\xd8", "prompt").strip()


def test_mock_coach_returns_nonempty_for_known_intents() -> None:
    c = MockCoach()
    for intent in ["what did they just ask", "summarize", "what did we decide"]:
        out = c.respond(intent, transcript="placeholder")
        assert out.strip()


@pytest.mark.parametrize(
    "text, max1, max2, expected1, expected2_nonempty",
    [
        ("Short answer", 28, 32, "Short answer", False),
        ("A longer answer that needs two lines", 20, 32, "A longer answer that", True),
        ("Multi  whitespace   here", 28, 32, "Multi whitespace here", False),  # normalized
    ],
)
def test_two_lines(text, max1, max2, expected1, expected2_nonempty) -> None:
    l1, l2 = _two_lines(text, max1=max1, max2=max2)
    assert l1 == expected1
    assert bool(l2) == expected2_nonempty


def test_memory_roundtrip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.sqlite"
        m = MemoryStore(str(db))

        eid = m.log_event(
            mode="visual",
            query="What is this?",
            response="Eastern red cedar",
            duration_s=1.4,
        )
        assert eid > 0

        events = m.recent_events(limit=5)
        assert len(events) == 1
        assert events[0]["mode"] == "visual"
        assert events[0]["response"] == "Eastern red cedar"
        assert events[0]["duration_s"] == 1.4


def test_memory_session_lifecycle() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.sqlite"
        m = MemoryStore(str(db))

        sid = m.start_session(label="Zahner Tuesday")
        assert sid > 0
        m.end_session(sid, transcript="...", summary="decided 16-ga steel")
        # End-session should not raise; presence is verified via no exception.
