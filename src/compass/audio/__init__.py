"""Audio capture and STT for verbal + retro modes. Phase 2."""

from compass.audio.buffer import MockRollingBuffer, RollingBuffer
from compass.audio.stt import STT, MockSTT

__all__ = ["MockRollingBuffer", "MockSTT", "RollingBuffer", "STT"]

try:
    # F401 is suppressed below: this import exists to re-export. The name is
    # appended to __all__ on the next line, which ruff cannot see statically
    # because __all__ here is built conditionally.
    from compass.audio.laptop_mic import LaptopMicBuffer  # noqa: F401

    __all__.append("LaptopMicBuffer")
except (ImportError, OSError):
    # ImportError: audio extra not installed.
    # OSError: sounddevice present but PortAudio (libportaudio2) missing.
    pass

try:
    # F401 is suppressed below: this import exists to re-export. The name is
    # appended to __all__ on the next line, which ruff cannot see statically
    # because __all__ here is built conditionally.
    from compass.audio.whisper_stt import WhisperSTT  # noqa: F401

    __all__.append("WhisperSTT")
except ImportError:
    pass
