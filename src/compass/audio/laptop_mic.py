"""Real audio capture using sounddevice + numpy ring buffer.

Per ADR 0006: RAM-only, never persisted. The ring buffer holds the last
N seconds of audio. snapshot() returns WAV-formatted bytes; the audio
format is 16kHz mono int16 (faster-whisper's preferred input).
"""

from __future__ import annotations

import io
import wave
from collections import deque
from threading import Lock

import numpy as np
import sounddevice as sd


class LaptopMicBuffer:
    """Rolling RAM buffer of laptop microphone audio.

    Parameters
    ----------
    sample_rate : int
        Hz. Default 16000 (Whisper-friendly).
    channels : int
        Default 1 (mono).
    max_seconds : float
        Ring buffer capacity. Default 1800 (30 minutes), matching ADR 0006.
    device : int | str | None
        sounddevice device index or substring. None = default input.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        max_seconds: float = 1800.0,
        device: int | str | None = None,
    ) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.max_samples = int(sample_rate * max_seconds)
        self.device = device
        self._ring: deque[np.ndarray] = deque()
        self._ring_samples = 0
        self._lock = Lock()
        self._stream: sd.InputStream | None = None
        self._closed = False

    # ARG002 is suppressed below: `time` is required by sounddevice's callback
    # signature (indata, frames, time, status); dropping it would break the stream.
    def _callback(self, indata: np.ndarray, frames: int, time, status) -> None:  # noqa: ANN001, ARG002
        if status:
            # Drop frames on overflow; never block the audio thread.
            return
        with self._lock:
            # Copy because indata is a numpy view into the audio driver's buffer.
            self._ring.append(indata.copy())
            self._ring_samples += frames
            while self._ring_samples > self.max_samples and self._ring:
                evicted = self._ring.popleft()
                self._ring_samples -= evicted.shape[0]

    def start(self) -> None:
        if self._closed:
            raise RuntimeError("Cannot start a closed buffer")
        if self._stream is not None:
            return
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="int16",
            device=self.device,
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> None:
        if self._stream is None:
            return
        self._stream.stop()
        self._stream = None
        # Buffer contents are preserved; only the input stream is paused.

    def snapshot(self, seconds: float | None = None) -> bytes:
        with self._lock:
            if not self._ring:
                return self._empty_wav()
            combined = np.concatenate(list(self._ring), axis=0)
        if seconds is not None:
            n_samples = int(seconds * self.sample_rate)
            combined = combined[-n_samples:]
        return self._to_wav_bytes(combined)

    def duration(self) -> float:
        if self._stream is None:
            return 0.0
        with self._lock:
            return self._ring_samples / self.sample_rate

    def close(self) -> None:
        self.stop()
        with self._lock:
            self._ring.clear()
            self._ring_samples = 0
        self._closed = True

    def _to_wav_bytes(self, samples: np.ndarray) -> bytes:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(self.channels)
            w.setsampwidth(2)  # int16
            w.setframerate(self.sample_rate)
            w.writeframes(samples.tobytes())
        return buf.getvalue()

    def _empty_wav(self) -> bytes:
        return self._to_wav_bytes(np.zeros((0, self.channels), dtype=np.int16))
