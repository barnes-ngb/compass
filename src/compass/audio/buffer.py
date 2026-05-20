"""Rolling audio buffer for retro mode. STUB for Phase 2.

Design notes (see docs/decisions/0006-memory-layers.md for the full ADR):

- The buffer is RAM-only. Raw audio is NEVER persisted. Period.
- When the user invokes retro mode, the buffer hands its current contents to
  the STT layer, which produces a transcript. The transcript may be persisted
  to the session log; the audio bytes are discarded immediately.
- Default buffer length: 30 minutes. Configurable via AUDIO_BUFFER_MINUTES.
- Always-armed in Phase 2+. In Phase 0–1, this stub is inert.
- Sessions in V0 are tap-to-tap: user explicitly starts and ends a session,
  and "always-armed buffer" only runs while a session is active. Phase 1
  may add auto-end heuristics (silence > N minutes, calendar end-time).
  Phase 2+ may remove the tap-to-start requirement entirely. See ADR 0006.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class RollingBuffer(Protocol):
    def start(self) -> None:
        """Begin armed capture. Audio fills the buffer until stop()."""
        ...

    def stop(self) -> None:
        """End armed capture. Buffer is cleared."""
        ...

    def snapshot(self, last_seconds: int) -> bytes:
        """Return raw audio bytes from the last `last_seconds`.

        Caller is responsible for handing this to STT and then discarding it.
        """
        ...

    def is_armed(self) -> bool: ...


class NullRollingBuffer:
    """Phase 0/1 placeholder. Raises if anyone tries to actually use it."""

    def start(self) -> None:
        raise NotImplementedError(
            "Audio capture is a Phase 2 feature. See docs/roadmap.md. "
            "Recommended dependency: sounddevice."
        )

    def stop(self) -> None: ...

    def snapshot(self, last_seconds: int) -> bytes:  # noqa: ARG002
        raise NotImplementedError("Audio capture is a Phase 2 feature.")

    def is_armed(self) -> bool:
        return False
