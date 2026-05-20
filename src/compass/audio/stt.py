"""Speech-to-text for verbal + retro modes. STUB for Phase 2.

Two providers in mind:

- LocalWhisper (`faster-whisper` with model="base.en"): ~2-3 s for 60 s of
  audio on a modern laptop CPU, fully private, free. Recommended default.
- CloudSTT: Deepgram, AssemblyAI, or eventually Anthropic when audio inputs
  are supported. ~0.5-1 s, costs ~$0.006/min, sends audio to vendor.

The pipeline doesn't care which; both implement the STT Protocol.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class STT(Protocol):
    """Speech-to-text. Stateless — every call is independent.

    Per ADR 0005, STT is invoked on-demand: in verbal mode it transcribes
    a short live capture; in retro mode it transcribes a RollingBuffer
    snapshot. Implementations may be local (faster-whisper) or cloud
    (Deepgram, AssemblyAI).
    """

    def transcribe(self, audio_bytes: bytes) -> str:
        """Return the transcribed text. Empty string for silence/unintelligible.
        Raises on backend errors (do not swallow)."""
        ...


class NullSTT:
    """Phase 0/1 placeholder. Raises if anyone tries to use it."""

    def transcribe(self, audio_bytes: bytes) -> str:  # noqa: ARG002
        raise NotImplementedError(
            "STT is a Phase 2 feature. Recommended local dependency: "
            "faster-whisper. See docs/decisions/0006-memory-layers.md."
        )
