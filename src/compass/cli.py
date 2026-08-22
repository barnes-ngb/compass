"""Wire config → providers → pipeline. Mode dispatch happens here."""

from __future__ import annotations

import argparse
import sys

from compass.audio.buffer import RollingBuffer
from compass.audio.stt import STT
from compass.coach.base import CoachProvider
from compass.config import Config, load_config
from compass.glasses.base import Glasses
from compass.memory.store import MemoryStore
from compass.pipeline import run_retro, run_verbal, run_visual
from compass.vision.base import VisionProvider


def _build_glasses(cfg: Config) -> Glasses:
    if cfg.glasses == "mock":
        from compass.glasses.mock import MockGlasses
        return MockGlasses(camera_index=cfg.camera_index)
    if cfg.glasses == "halo":
        import importlib.util
        if importlib.util.find_spec("brilliant_msg") is None:
            raise SystemExit(
                "GLASSES=halo requires Halo hardware and its SDK. "
                "Install with: pip install brilliant-msg — deliberately NOT in "
                "the project extras until hardware arrives (ADR 0009)."
            )
        from compass.glasses.halo import HaloGlasses
        return HaloGlasses()
    if cfg.glasses == "frame":
        from compass.glasses.frame import FrameGlasses
        return FrameGlasses()
    raise SystemExit(f"Unknown GLASSES={cfg.glasses!r}. Use 'mock', 'halo', or 'frame'.")


def _build_vision(cfg: Config) -> VisionProvider:
    if cfg.vision_provider == "mock":
        from compass.vision.mock import MockVision
        return MockVision()
    if cfg.vision_provider == "claude":
        from compass.vision.claude import ClaudeVision
        return ClaudeVision(api_key=cfg.anthropic_api_key or "", model=cfg.claude_model)
    if cfg.vision_provider == "gemini":
        from compass.vision.gemini import GeminiVision
        return GeminiVision(api_key=cfg.gemini_api_key or "")
    raise SystemExit(f"Unknown VISION_PROVIDER={cfg.vision_provider!r}.")


def _build_audio_buffer(cfg: Config) -> RollingBuffer:
    if cfg.audio_buffer == "mock":
        from compass.audio.buffer import MockRollingBuffer
        return MockRollingBuffer()
    if cfg.audio_buffer == "laptop":
        try:
            from compass.audio.laptop_mic import LaptopMicBuffer
        except ImportError as exc:
            raise SystemExit(
                "AUDIO_BUFFER=laptop requires the audio extra. "
                'Install with: pip install -e ".[audio]"'
            ) from exc
        return LaptopMicBuffer(max_seconds=cfg.audio_buffer_minutes * 60.0)
    raise SystemExit(f"Unknown AUDIO_BUFFER={cfg.audio_buffer!r}. Use 'mock' or 'laptop'.")


def _build_stt(cfg: Config) -> STT:
    if cfg.stt_provider == "mock":
        from compass.audio.stt import MockSTT
        return MockSTT()
    if cfg.stt_provider == "whisper":
        try:
            from compass.audio.whisper_stt import WhisperSTT
        except ImportError as exc:
            raise SystemExit(
                "STT_PROVIDER=whisper requires the audio extra. "
                'Install with: pip install -e ".[audio]"'
            ) from exc
        return WhisperSTT(model_name=cfg.whisper_model)
    raise SystemExit(f"Unknown STT_PROVIDER={cfg.stt_provider!r}. Use 'mock' or 'whisper'.")


def _build_coach(cfg: Config) -> CoachProvider:
    if cfg.coach_provider == "mock":
        from compass.coach.mock import MockCoach
        return MockCoach()
    if cfg.coach_provider == "claude":
        from compass.coach.claude import ClaudeCoach
        return ClaudeCoach(api_key=cfg.anthropic_api_key or "", model=cfg.coach_model)
    raise SystemExit(f"Unknown COACH_PROVIDER={cfg.coach_provider!r}.")


def main() -> None:
    parser = argparse.ArgumentParser(prog="compass", description="An AI coach for your world.")
    parser.add_argument(
        "--mode",
        choices=["visual", "verbal", "retro"],
        help="Override MODE in .env. Default: visual.",
    )
    args = parser.parse_args()

    cfg = load_config()
    mode = (args.mode or cfg.mode).lower()

    print(
        f"[compass] mode={mode} glasses={cfg.glasses} "
        f"vision={cfg.vision_provider} coach={cfg.coach_provider}"
    )

    try:
        glasses = _build_glasses(cfg)
        memory = MemoryStore(cfg.memory_db)
    except (ValueError, SystemExit) as exc:
        print(f"Startup error: {exc}", file=sys.stderr)
        sys.exit(1)

    if mode == "visual":
        vision = _build_vision(cfg)
        run_visual(glasses, vision, memory, prompt=cfg.vision_prompt)
    elif mode == "verbal":
        coach = _build_coach(cfg)
        buffer = _build_audio_buffer(cfg)
        stt = _build_stt(cfg)
        run_verbal(glasses, buffer, stt, coach, memory, capture_seconds=cfg.verbal_capture_seconds)
    elif mode == "retro":
        coach = _build_coach(cfg)
        buffer = _build_audio_buffer(cfg)
        stt = _build_stt(cfg)
        run_retro(glasses, buffer, stt, coach, memory)
    else:
        raise SystemExit(f"Unknown mode {mode!r}. Use visual, verbal, or retro.")


if __name__ == "__main__":
    main()
