"""Mode-aware orchestration: visual / verbal / retro.

All three modes share the Glasses + memory infrastructure. They diverge in
where the input comes from (camera / mic-now / mic-buffer) and which provider
handles the inference (vision vs coach).

Status: visual, verbal, and retro all run end-to-end against mock or laptop
implementations. Verbal captures a fixed window of the wearer's own speech on
trigger and treats it as the question; retro snapshots the rolling buffer and
asks a fixed recall question of it; visual captures a frame. All three share
the Glasses + memory infrastructure.
"""

from __future__ import annotations

import time

from compass.audio.buffer import RollingBuffer
from compass.audio.stt import STT
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
    session_id = memory.start_session(label="visual")
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
            memory.log_event(
                mode="visual",
                query=prompt,
                response=answer,
                duration_s=dt,
                session_id=session_id,
            )
    finally:
        _finalize_session(memory, session_id)
        glasses.close()


def run_verbal(
    glasses: Glasses,
    buffer: RollingBuffer,
    stt: STT,
    coach: CoachProvider,
    memory: MemoryStore,
    capture_seconds: float = 8.0,
    context_seconds: float = 120.0,
) -> None:
    """Trigger → fresh capture → STT → coach → HUD.

    The wearer presses the trigger, then speaks a question. The rolling
    buffer is already running; after `capture_seconds` the pipeline
    snapshots that window and transcribes it — that transcript IS the
    query. A pre-trigger snapshot of the last `context_seconds` is passed
    to the coach as conversational context.

    This is the inverse of retro mode: there the intent is fixed and the
    transcript is the material; here the transcript is the intent and the
    buffer is the material. V0 uses a fixed capture window with no wake
    word (ADR 0005); silence detection is a V1 concern (docs/roadmap.md
    Phase 3). Audio stays in RAM and is never persisted (ADR 0006).
    """
    glasses.connect()
    session_id = memory.start_session(label="verbal")
    buffer.start()
    try:
        glasses.show_text("Compass ready", "SPACE = ask", color="cloudblue")
        while True:
            if not glasses.wait_for_trigger():
                break

            # Context first — taken BEFORE the listening window so it holds the
            # conversation leading up to the question, not the question itself.
            context_audio = buffer.snapshot(seconds=context_seconds)

            glasses.show_text(
                "Listening...", f"speak now ({capture_seconds:.0f}s)", color="yellow"
            )
            if capture_seconds > 0:
                time.sleep(capture_seconds)

            t0 = time.perf_counter()
            try:
                question_audio = buffer.snapshot(seconds=capture_seconds)
                question_text = stt.transcribe(question_audio).strip()
                if not question_text:
                    glasses.show_text("(heard nothing)", color="grey")
                    continue
                context_text = stt.transcribe(context_audio).strip() if context_audio else ""

                glasses.show_text("Thinking...", color="yellow")
                memory_context = ""  # Phase 3 will populate from recent sessions
                answer = coach.respond(
                    intent=question_text,
                    transcript=context_text,
                    memory_context=memory_context,
                )
            except Exception as exc:  # noqa: BLE001
                glasses.show_text("Verbal error", str(exc)[:32], color="red")
                continue
            dt = time.perf_counter() - t0

            if not answer:
                glasses.show_text("(no answer)", color="grey")
                continue

            line1, line2 = _two_lines(answer, max1=28, max2=32)
            glasses.show_text(line1, line2 or f"{dt:.1f}s", color="green")

            memory.log_event(
                mode="verbal",
                query=question_text,
                response=answer,
                duration_s=dt,
                session_id=session_id,
            )
    finally:
        _finalize_session(memory, session_id, coach)
        buffer.close()
        glasses.close()


def run_retro(
    glasses: Glasses,
    buffer: RollingBuffer,
    stt: STT,
    coach: CoachProvider,
    memory: MemoryStore,
    intent: str = "what did they just ask about",
    snapshot_seconds: float = 300.0,
) -> None:
    """Button-press → buffer snapshot → STT → coach → HUD.

    The rolling audio buffer runs during the session (RAM only, never persisted).
    On button-press, the last `snapshot_seconds` of audio is transcribed and
    passed to the coach with current memory context. The coach returns a short
    HUD directive.
    """
    glasses.connect()
    session_id = memory.start_session(label="retro")
    buffer.start()
    try:
        glasses.show_text("Compass ready", "SPACE = ask retro", color="cloudblue")
        while True:
            if not glasses.wait_for_trigger():
                break
            glasses.show_text("Listening back...", color="yellow")

            t0 = time.perf_counter()
            try:
                audio = buffer.snapshot(seconds=snapshot_seconds)
                transcript = stt.transcribe(audio)
                memory_context = ""  # Phase 3 will populate from recent sessions
                answer = coach.respond(intent, transcript, memory_context)
            except Exception as exc:  # noqa: BLE001
                glasses.show_text("Retro error", str(exc)[:32], color="red")
                continue
            dt = time.perf_counter() - t0

            if not answer:
                glasses.show_text("(no answer)", color="grey")
                continue

            line1, line2 = _two_lines(answer, max1=28, max2=32)
            glasses.show_text(line1, line2 or f"{dt:.1f}s", color="green")

            memory.log_event(
                mode="retro",
                query=intent,
                response=answer,
                duration_s=dt,
                session_id=session_id,
            )
    finally:
        _finalize_session(memory, session_id, coach)
        buffer.close()
        glasses.close()


# ---- helpers ----------------------------------------------------------------


def _finalize_session(
    memory: MemoryStore,
    session_id: int,
    coach: CoachProvider | None = None,
) -> None:
    """Assemble the session transcript from its events and persist a summary.

    Called once per run, on loop exit. V0 has no continuous STT; the event log
    is the record, so the transcript is built from the session's events. If a
    coach is provided, it produces the summary via the same respond() interface
    used for live directives (ADR 0006: one interface, different payload).
    Visual sessions carry no coach and store the transcript only. A failure
    here never masks the real shutdown path.
    """
    try:
        events = memory.events_for_session(session_id)
        transcript = "\n".join(
            f"Q: {e['query']}\nA: {e['response']}" for e in events
        )
        summary = ""
        if coach is not None and transcript:
            summary = coach.respond("summarize this session", transcript, "")
        memory.end_session(session_id, transcript=transcript, summary=summary)
    except Exception:  # noqa: BLE001 — shutdown must not crash on a summary failure
        try:
            memory.end_session(session_id)
        except Exception:  # noqa: BLE001
            pass


def _two_lines(text: str, max1: int, max2: int) -> tuple[str, str]:
    """Wrap a short string to two HUD lines without breaking words if possible."""
    text = " ".join(text.split())
    if len(text) <= max1:
        return text, ""
    split_at = text.rfind(" ", 0, max1 + 1)
    if split_at <= 0:
        split_at = max1
    return text[:split_at].rstrip(), text[split_at:].lstrip()[:max2]
