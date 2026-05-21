"""Audio capture and STT for verbal + retro modes. Phase 2."""

from compass.audio.buffer import MockRollingBuffer, RollingBuffer
from compass.audio.stt import MockSTT, STT

__all__ = ["MockRollingBuffer", "MockSTT", "RollingBuffer", "STT"]

try:
    from compass.audio.laptop_mic import LaptopMicBuffer

    __all__.append("LaptopMicBuffer")
except (ImportError, OSError):
    # ImportError: audio extra not installed.
    # OSError: sounddevice present but PortAudio (libportaudio2) missing.
    pass
