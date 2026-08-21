"""Speech-to-text for verbal + retro modes.

Defines the `STT` Protocol and its inert placeholder (`NullSTT`) and
deterministic test double (`MockSTT`). The real implementation, `WhisperSTT`,
lives in `whisper_stt.py` and is selected with STT_PROVIDER=whisper.

- `WhisperSTT` (`faster-whisper`, default model "small.en", override with
  WHISPER_MODEL): runs locally on the laptop CPU, fully private, free. This is
  the shipped provider. "base.en" is the faster, less accurate alternative.
- Cloud STT remains a future option: Deepgram, AssemblyAI, or eventually
  Anthropic when audio inputs are supported. ~0.5-1 s, costs ~$0.006/min,
  sends audio to a vendor. Not implemented.

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


class MockSTT:
    """Deterministic STT for testing retro-mode wiring.

    Treats the audio_bytes payload as already-UTF-8-encoded text and decodes
    it. This pairs with MockRollingBuffer, which encodes its canned transcript
    to UTF-8 in snapshot(). Returns the decoded string; returns "" for empty input.
    """

    def transcribe(self, audio_bytes: bytes) -> str:
        if not audio_bytes:
            return ""
        try:
            return audio_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return "[unintelligible mock audio]"
