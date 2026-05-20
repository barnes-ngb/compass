"""Mode-aware orchestration: visual / verbal / retro.

All three modes share the Glasses + memory infrastructure. They diverge in
where the input comes from (camera / mic-now / mic-buffer) and which provider
handles the inference (vision vs coach).

Phase 0 status: visual mode runs end-to-end against the mock glasses. Verbal
and retro modes are scaffolded but raise NotImplementedError — they will light
up once we wire the audio buffer and STT in Phase 2.
"""

from __future__ import annotations

import time

from compass.coach.base import CoachProvider
from compass.glasses.base import Glasses
from compass.memory.store import MemoryStore
from compass.vision.base import VisionProvider


def run_visual(
    glasses: Glasses,
    vision: VisionProvider,
    memory: MemoryStore,
    prompt: str,
) -> None:
    """Capture → VLM → HUD. The original glance-to-directive loop."""
    glasses.connect()
    try:
        glasses.show_text("Compass ready", "SPACE = capture", color="cloudblue")
        while True:
            if not glasses.wait_for_trigger():
                break
            glasses.show_text("Capturing...", color="yellow")
            image = glasses.capture_image()

            glasses.show_text("Thinking...", color="yellow")
            t0 = time.perf_counter()
            try:
                answer = vision.describe(image, prompt)
            except Exception as exc:  # noqa: BLE001
                glasses.show_text("Vision error", str(exc)[:32], color="red")
                continue
            dt = time.perf_counter() - t0

            if not answer:
                glasses.show_text("(no answer)", color="grey")
                continue

            line1, line2 = _two_lines(answer, max1=28, max2=32)
            glasses.show_text(line1, line2 or f"{dt:.1f}s", color="green")

            # Memory: log every visual query so they're queryable later.
            memory.log_event(mode="visual", query=prompt, response=answer, duration_s=dt)
    finally:
        glasses.close()


def run_verbal(
    glasses: Glasses,
    coach: CoachProvider,  # noqa: ARG001 — Phase 2 stub
    memory: MemoryStore,  # noqa: ARG001
) -> None:
    """Voice trigger → STT → coach → HUD. Phase 2."""
    raise NotImplementedError(
        "Verbal mode is a Phase 2 stub. Needs the audio capture layer "
        "(sounddevice) and STT (faster-whisper) wired in. "
        "See docs/decisions/0005-coach-modes.md and docs/roadmap.md."
    )


def run_retro(
    glasses: Glasses,
    coach: CoachProvider,  # noqa: ARG001
    memory: MemoryStore,  # noqa: ARG001
) -> None:
    """Button-press → process rolling buffer → coach → HUD. Phase 2.

    The rolling audio buffer is always armed (RAM only, never persisted).
    On button-press, the last N minutes of audio is transcribed and passed
    to the coach with current memory context. The coach returns a short
    HUD directive ("they asked about Q3 numbers", "you decided 16-ga steel").
    """
    raise NotImplementedError(
        "Retro mode is a Phase 2 stub. Needs the rolling buffer "
        "(audio/buffer.py), STT (audio/stt.py), and the coach provider "
        "wired together. See docs/decisions/0005-coach-modes.md and "
        "docs/decisions/0006-memory-layers.md."
    )


# ---- helpers ----------------------------------------------------------------


def _two_lines(text: str, max1: int, max2: int) -> tuple[str, str]:
    """Wrap a short string to two HUD lines without breaking words if possible."""
    text = " ".join(text.split())
    if len(text) <= max1:
        return text, ""
    split_at = text.rfind(" ", 0, max1 + 1)
    if split_at <= 0:
        split_at = max1
    return text[:split_at].rstrip(), text[split_at:].lstrip()[:max2]
