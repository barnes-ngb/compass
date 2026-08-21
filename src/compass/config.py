"""Configuration loaded from environment (or .env).

All env-fiddling lives here so the rest of the code imports clean Python
constants. Easier to test, easier to change.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()  # no-op if .env missing


@dataclass(frozen=True)
class Config:
    # Mode
    mode: str  # visual | verbal | retro

    # Vision (visual mode)
    vision_provider: str
    anthropic_api_key: str | None
    claude_model: str
    gemini_api_key: str | None
    vision_prompt: str

    # Coach (verbal + retro modes)
    coach_provider: str
    coach_model: str

    # Glasses
    glasses: str
    camera_index: int

    # Memory
    memory_db: str

    # Audio / STT (verbal + retro modes)
    audio_buffer: str
    audio_buffer_minutes: int
    stt_provider: str
    whisper_model: str
    verbal_capture_seconds: float


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def load_config() -> Config:
    return Config(
        mode=_env("MODE", "visual").lower(),
        vision_provider=_env("VISION_PROVIDER", "claude").lower(),
        anthropic_api_key=_env("ANTHROPIC_API_KEY") or None,
        claude_model=_env("CLAUDE_MODEL", "claude-sonnet-4-6"),
        gemini_api_key=_env("GEMINI_API_KEY") or None,
        vision_prompt=_env(
            "VISION_PROMPT",
            "Describe what you see in 1–2 short phrases (under 18 words total). "
            "If the image contains drawings, dimensions, materials, fasteners, "
            "panels, fabrication marks, part numbers, or anything that looks "
            "shop- or build-relevant, surface those first. Otherwise just "
            "describe the scene plainly.",
        ),
        coach_provider=_env("COACH_PROVIDER", "claude").lower(),
        coach_model=_env("COACH_MODEL", "claude-sonnet-4-6"),
        glasses=_env("GLASSES", "mock").lower(),
        camera_index=int(_env("CAMERA_INDEX", "0")),
        memory_db=_env("MEMORY_DB", "./compass-memory.sqlite"),
        audio_buffer=_env("AUDIO_BUFFER", "mock").lower(),
        audio_buffer_minutes=int(_env("AUDIO_BUFFER_MINUTES", "30")),
        stt_provider=_env("STT_PROVIDER", "mock").lower(),
        whisper_model=_env("WHISPER_MODEL", "small.en"),
        verbal_capture_seconds=float(_env("VERBAL_CAPTURE_SECONDS", "8.0")),
    )
