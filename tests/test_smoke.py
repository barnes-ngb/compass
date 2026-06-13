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

from compass.audio.buffer import MockRollingBuffer, RollingBuffer
from compass.audio.stt import MockSTT, STT
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


def test_mock_rolling_buffer_satisfies_protocol() -> None:
    buf = MockRollingBuffer()
    assert isinstance(buf, RollingBuffer)


def test_mock_stt_satisfies_protocol() -> None:
    stt = MockSTT()
    assert isinstance(stt, STT)


def test_laptop_mic_buffer_satisfies_protocol_if_installed() -> None:
    """LaptopMicBuffer must satisfy RollingBuffer when sounddevice is available."""
    try:
        from compass.audio.laptop_mic import LaptopMicBuffer
    except (ImportError, OSError):
        pytest.skip("sounddevice/PortAudio not available; LaptopMicBuffer unavailable")

    # Don't actually start the stream in tests — just check the protocol shape.
    buf = LaptopMicBuffer()
    from compass.audio.buffer import RollingBuffer
    assert isinstance(buf, RollingBuffer)


def test_whisper_stt_satisfies_protocol_if_installed() -> None:
    """WhisperSTT must satisfy STT when faster-whisper is available.

    Skipped if faster-whisper isn't installed. Does NOT actually run inference
    (model download would dominate test time).
    """
    try:
        from compass.audio.whisper_stt import WhisperSTT  # noqa: F401
    except ImportError:
        pytest.skip("faster-whisper not installed; WhisperSTT unavailable")

    # We don't instantiate (would download the model). Just check the class
    # has the right shape for STT Protocol by inspecting the method signature.
    import inspect
    sig = inspect.signature(WhisperSTT.transcribe)
    assert "audio_bytes" in sig.parameters
    assert sig.return_annotation in (str, "str")


def test_whisper_stt_accepts_model_name_param() -> None:
    """WhisperSTT accepts a model_name parameter and defaults to small.en.

    Does NOT instantiate (would download the model). Just checks signature.
    """
    try:
        from compass.audio.whisper_stt import WhisperSTT  # noqa: F401
    except ImportError:
        import pytest
        pytest.skip("faster-whisper not installed; WhisperSTT unavailable")

    import inspect
    sig = inspect.signature(WhisperSTT.__init__)
    assert "model_name" in sig.parameters
    assert sig.parameters["model_name"].default == "small.en"


def test_mock_audio_roundtrip() -> None:
    """Buffer + STT round-trip: canned transcript → bytes → STT → original string."""
    buf = MockRollingBuffer(canned_transcript="hello compass")
    buf.start()
    audio = buf.snapshot()
    stt = MockSTT()
    assert stt.transcribe(audio) == "hello compass"
    buf.close()


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


class _TestGlasses:
    """Programmatic test fixture — one trigger, then exit."""
    def __init__(self) -> None:
        self._fired = False
        self.last_text: tuple[str, str] | None = None

    def connect(self) -> None: ...

    def wait_for_trigger(self) -> bool:
        if self._fired:
            return False
        self._fired = True
        return True

    def capture_image(self) -> bytes:
        return b""

    def show_text(self, line1: str, line2: str = "", *, color: str = "green") -> None:
        self.last_text = (line1, line2)

    def close(self) -> None: ...


def test_run_retro_loops_once_and_logs() -> None:
    """Retro mode: one synthetic trigger → buffer → STT → coach → memory logged."""
    import tempfile
    from compass.memory.store import MemoryStore
    from compass.audio.buffer import MockRollingBuffer
    from compass.audio.stt import MockSTT
    from compass.coach.mock import MockCoach
    from compass.pipeline import run_retro

    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tmp:
        db_path = tmp.name
    memory = MemoryStore(db_path=db_path)

    glasses = _TestGlasses()
    buffer = MockRollingBuffer(canned_transcript="they asked about Q3 panel schedule")
    stt = MockSTT()
    coach = MockCoach()

    run_retro(glasses, buffer, stt, coach, memory)

    # One event should be logged in retro mode.
    events = memory.recent_events(limit=5)
    assert len(events) == 1
    assert events[0]["mode"] == "retro"
    assert events[0]["response"]  # non-empty


def test_run_verbal_loops_once_and_logs() -> None:
    """Verbal mode: one synthetic trigger -> record -> STT -> coach -> memory logged."""
    import tempfile
    from compass.memory.store import MemoryStore
    from compass.audio.buffer import MockRollingBuffer
    from compass.audio.stt import MockSTT
    from compass.coach.mock import MockCoach
    from compass.pipeline import run_verbal

    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tmp:
        db_path = tmp.name
    memory = MemoryStore(db_path=db_path)

    glasses = _TestGlasses()
    buffer = MockRollingBuffer(canned_transcript="how should I detail this parapet")
    stt = MockSTT()
    coach = MockCoach()

    # listen_seconds=0.0 so the test does not actually sleep.
    run_verbal(glasses, buffer, stt, coach, memory, listen_seconds=0.0)

    events = memory.recent_events(limit=5)
    assert len(events) == 1
    assert events[0]["mode"] == "verbal"
    assert events[0]["response"]  # non-empty


def test_run_verbal_creates_and_finalizes_session() -> None:
    """One verbal run opens a session, logs an event under it, and finalizes
    the session with a transcript and a coach summary on exit."""
    import tempfile
    from compass.memory.store import MemoryStore
    from compass.audio.buffer import MockRollingBuffer
    from compass.audio.stt import MockSTT
    from compass.coach.mock import MockCoach
    from compass.pipeline import run_verbal

    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tmp:
        db_path = tmp.name
    memory = MemoryStore(db_path=db_path)

    glasses = _TestGlasses()
    buffer = MockRollingBuffer(canned_transcript="how should I detail this parapet")
    stt = MockSTT()
    coach = MockCoach()

    run_verbal(glasses, buffer, stt, coach, memory, listen_seconds=0.0)

    events = memory.recent_events(limit=5)
    assert len(events) == 1
    session_id = events[0]["session_id"]
    assert session_id is not None  # event is tied to a session

    session = memory.get_session(session_id)
    assert session is not None
    assert session["ended_ts"] is not None      # finalized on exit
    assert session["label"] == "verbal"
    assert session["transcript"]                 # assembled from events
    assert session["summary"]                    # coach summary (MockCoach 'summar' branch)


def test_memory_session_lifecycle() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.sqlite"
        m = MemoryStore(str(db))

        sid = m.start_session(label="Zahner Tuesday")
        assert sid > 0
        m.end_session(sid, transcript="...", summary="decided 16-ga steel")
        # End-session should not raise; presence is verified via no exception.
