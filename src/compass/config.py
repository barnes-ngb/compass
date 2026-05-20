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

    # Audio / STT (Phase 2)
    audio_buffer_minutes: int
    stt_provider: str
    whisper_model: str


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
            "In 8 words or fewer, name the most prominent subject. No punctuation.",
        ),
        coach_provider=_env("COACH_PROVIDER", "claude").lower(),
        coach_model=_env("COACH_MODEL", "claude-sonnet-4-6"),
        glasses=_env("GLASSES", "mock").lower(),
        camera_index=int(_env("CAMERA_INDEX", "0")),
        memory_db=_env("MEMORY_DB", "./compass-memory.sqlite"),
        audio_buffer_minutes=int(_env("AUDIO_BUFFER_MINUTES", "30")),
        stt_provider=_env("STT_PROVIDER", "local").lower(),
        whisper_model=_env("WHISPER_MODEL", "base.en"),
    )
