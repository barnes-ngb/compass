"""Rolling audio buffer for verbal + retro modes.

Defines the `RollingBuffer` Protocol and its inert placeholder
(`NullRollingBuffer`) and deterministic test double (`MockRollingBuffer`).
The real implementation, `LaptopMicBuffer`, lives in `laptop_mic.py` and is
selected with AUDIO_BUFFER=laptop. Two of the three modes take a buffer:
verbal pulls a short pre-trigger context window alongside the live capture,
retro transcribes a snapshot of it. Visual mode does not use one at all.

Design notes (see docs/decisions/0006-memory-layers.md for the full ADR):

- The buffer is RAM-only. Raw audio is NEVER persisted. Period.
- When the user invokes retro mode, the buffer hands its current contents to
  the STT layer, which produces a transcript. The transcript may be persisted
  to the session log; the audio bytes are discarded immediately.
- Default buffer length: 30 minutes. Configurable via AUDIO_BUFFER_MINUTES.
- Sessions in V0 are tap-to-tap: user explicitly starts and ends a session,
  and "always-armed buffer" only runs while a session is active. Phase 1
  may add auto-end heuristics (silence > N minutes, calendar end-time).
  Phase 2+ may remove the tap-to-start requirement entirely. See ADR 0006.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class RollingBuffer(Protocol):
    """Rolling audio buffer. RAM-only, never persisted.

    Per docs/decisions/0006-memory-layers.md, the buffer is the lowest
    layer of the memory pipeline. It holds the last N minutes of audio,
    overwriting oldest as new audio comes in. Raw audio bytes never leave
    the in-memory buffer; only STT-derived transcripts are persisted.
    """

    def start(self) -> None:
        """Begin capturing audio from the configured input device.
        Idempotent — calling start() on an already-started buffer is a no-op."""
        ...

    def stop(self) -> None:
        """Stop capturing audio. The buffer's contents may still be queried
        via snapshot() until close() is called."""
        ...

    def snapshot(self, seconds: float | None = None) -> bytes:
        """Return the last `seconds` of audio as a single bytes blob (WAV format).
        If seconds is None, return the entire buffer contents."""
        ...

    def duration(self) -> float:
        """Return the current buffer fill, in seconds.
        Returns 0.0 if the buffer hasn't been started yet."""
        ...

    def close(self) -> None:
        """Release the input device and clear the buffer."""
        ...


class NullRollingBuffer:
    """Phase 0/1 placeholder. Raises if anyone tries to actually use it."""

    def start(self) -> None:
        raise NotImplementedError(
            "Audio capture is a Phase 2 feature. See docs/roadmap.md. "
            "Recommended dependency: sounddevice."
        )

    def stop(self) -> None: ...

    def snapshot(self, seconds: float | None = None) -> bytes:  # noqa: ARG002
        raise NotImplementedError("Audio capture is a Phase 2 feature.")

    def duration(self) -> float:
        return 0.0

    def close(self) -> None: ...


class MockRollingBuffer:
    """Deterministic in-memory buffer for testing retro mode wiring.

    Holds a configurable canned transcript snippet. start()/stop() flip an
    internal flag; snapshot() returns a small bytes payload (the canned
    transcript encoded as UTF-8) so STT can transcribe a known string back.
    duration() returns a fake elapsed-time counter that advances with each
    snapshot() call (lets retro-mode tests reason about time without real audio).
    """

    def __init__(self, canned_transcript: str = "what did they just ask about Q3 panels") -> None:
        self._canned = canned_transcript
        self._started = False
        self._fake_seconds = 0.0
        self._closed = False

    def start(self) -> None:
        if self._closed:
            raise RuntimeError("Cannot start a closed buffer")
        self._started = True

    def stop(self) -> None:
        self._started = False

    def snapshot(self, seconds: float | None = None) -> bytes:  # noqa: ARG002
        self._fake_seconds += 30.0
        return self._canned.encode("utf-8")

    def duration(self) -> float:
        return self._fake_seconds if self._started else 0.0

    def close(self) -> None:
        self._closed = True
        self._started = False
