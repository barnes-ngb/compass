"""Local STT using faster-whisper.

Default model: 'base.en'. ~75MB, English-only, runs on CPU in 1-3 seconds
for a 5-minute audio snapshot on a modern laptop. The model downloads once
and caches to disk at faster-whisper's default cache location.
"""

from __future__ import annotations

import io
import wave
from typing import Any

import numpy as np


class WhisperSTT:
    """Local STT via faster-whisper.

    The first instantiation downloads the model (~75MB for base.en).
    Subsequent runs load from cache.

    Parameters
    ----------
    model_name : str
        faster-whisper model name. Default 'base.en'.
    device : str
        'cpu' (default) or 'cuda'. CPU is fine for laptop use.
    compute_type : str
        Default 'int8' for speed; 'float16' or 'float32' for quality.
    """

    def __init__(
        self,
        model_name: str = "base.en",
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        # Defer the heavy import so MockSTT users don't pay for it.
        from faster_whisper import WhisperModel  # type: ignore[import-not-found]
        self._model: Any = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type,
        )

    def transcribe(self, audio_bytes: bytes) -> str:
        if not audio_bytes:
            return ""
        # faster-whisper accepts a numpy float32 mono array at 16kHz.
        samples = self._wav_bytes_to_float32(audio_bytes)
        if samples.size == 0:
            return ""
        segments, _info = self._model.transcribe(samples, language="en")
        return " ".join(seg.text.strip() for seg in segments).strip()

    @staticmethod
    def _wav_bytes_to_float32(wav_bytes: bytes) -> np.ndarray:
        with wave.open(io.BytesIO(wav_bytes), "rb") as w:
            n_frames = w.getnframes()
            raw = w.readframes(n_frames)
            sampwidth = w.getsampwidth()
            channels = w.getnchannels()
        # Assume int16 mono (what LaptopMicBuffer produces).
        if sampwidth != 2:
            raise ValueError(f"Expected 16-bit PCM, got {sampwidth*8}-bit")
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        if channels > 1:
            samples = samples.reshape(-1, channels).mean(axis=1)
        return samples
