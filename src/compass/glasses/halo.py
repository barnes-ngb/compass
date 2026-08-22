"""Halo Glasses driver — PRE-HARDWARE SKETCH.

Written against the merged firmware inspection report
`docs/inspection/2026-08-19-halo-firmware-protocol.md` (audited upstream:
halo-firmware `main` @ `9a306ae7072d84a94f377e1b857d47d30ddaf014`) and the
`brilliant_sdk` repo docs (brilliant-msg README + CHANGELOG 7.1.0, "true-up
against Halo firmware 0.8.8"). Citations below use:

    inspection §n.n     = PROTOCOL.md section per the report
    msg README/CHANGELOG = brilliant_sdk python/packages/brilliant_msg docs

This class HAS NEVER RUN ON HARDWARE. Every unverifiable call shape is
marked ``TODO(hardware):`` — the union of those comments is the hardware-day
checklist. Hardware ships ~September 2026 (ADR 0008/0009).
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import threading
from pathlib import Path
from typing import Any

# --- compass's tiny framing on the user-data channel -------------------------
# The inspection report ("Lua runtime surface": compass defines its own tiny
# framing — text+color in, JPEG/audio chunks out) leaves the message codes to
# us. Values below follow frame-msg lineage (brilliant_sdk ships MIGRATION.md
# from frame-msg) so the documented Rx classes have the best chance of parsing
# them unchanged.
# TODO(hardware): true these codes up against brilliant-msg's actual std msg
# codes (inspection §Gaps Q2 — the framing layer is undocumented in the
# firmware repo) and confirm no collision with its own reserved codes.
MSG_TEXT = 0x0A       # host -> device: "RRGGBB\nline1\nline2" (compass-defined)
MSG_CAPTURE = 0x0D    # host -> device: 1 quality byte (compass-defined)
MSG_AUDIO_CTL = 0x30  # host -> device: 0x01 start mic / 0x00 stop (compass-defined)
MSG_TAP = 0x09        # device -> host: tap kind bytes, parsed by RxTap (msg CHANGELOG)
MSG_PHOTO = 0x07      # device -> host: JPEG chunks, assembled by RxPhoto (msg CHANGELOG)
MSG_AUDIO = 0x05      # device -> host: mic chunks, parsed by RxAudio (msg CHANGELOG)

# Only quality levels documented for Halo capture, largest to smallest
# (~80/47/25/16 KB JPEGs) — inspection §7.11.
QUALITY_LEVELS = ("VERY_HIGH", "HIGH", "MEDIUM", "LOW")

# Compass color names -> 0xRRGGBB. Same palette as MockGlasses (mock.py stores
# BGR for OpenCV; these are the RGB equivalents). Halo's display.text takes a
# 24-bit RGB color per call — inspection §7.10.
COLORS = {
    "void": 0x10101C,
    "white": 0xF0F0F0,
    "grey": 0xA0A0A0,
    "red": 0xE6283C,
    "green": 0x50DC50,
    "yellow": 0xE6DC28,
    "cloudblue": 0x78C8DC,
}

# Halo renders Dogica 8px at 30 chars/line (msg CHANGELOG 7.1.0), so line2
# truncates at 30; line1 keeps parity with MockGlasses at 28 (< 30, so still
# safe). MockGlasses used to allow 32 on line2 and now clips at 30 to match
# — the simulator must not be more generous than the hardware.
# TODO(hardware): the firmware repo itself doesn't document chars-per-line
# (inspection §show_text row: "verify on hardware") — confirm 30 holds at the
# font size halo.lua actually sets.
LINE1_MAX = 28
LINE2_MAX = 30


class HaloGlasses:
    """Brilliant Labs Halo driver implementing the `Glasses` Protocol.

    PRE-HARDWARE SKETCH — never run on real glasses. Written against
    `docs/inspection/2026-08-19-halo-firmware-protocol.md` (halo-firmware
    `main` @ `9a306ae7072d84a94f377e1b857d47d30ddaf014`) and brilliant-msg
    7.1.0 docs. `TODO(hardware):` comments mark every unverified seam.

    Architecture: the host talks brilliant-msg over BLE; the on-device half
    is `halo.lua` (same directory), uploaded and started by `connect()` per
    ADR 0009 §6. Camera and mic bytes are Lua-pumped over the user-data
    channel — the firmware exposes no host-direct path for them (inspection
    §Gaps Q1).

    Async bridging: the brilliant SDK is async; the `Glasses` Protocol is
    sync. This class holds ONE private event loop on a daemon thread and
    bridges each method with `run_coroutine_threadsafe`, rather than calling
    `asyncio.run()` per method. Rationale: the BLE client and its
    notification subscriptions (tap events, photo chunks) must stay alive
    *between* Protocol calls — `asyncio.run()` would close the loop the
    client is bound to after every call and drop the GATT subscriptions.
    TODO(hardware): real-hardware testing may force revisiting this (e.g. if
    brilliant-msg spawns its own loop or dislikes cross-thread use).

    Trigger gestures (inspection §7.4/§7.6; BUTTON_LED_GUIDE §Quick
    Reference): single tap (IMU or button) = capture trigger; DOUBLE tap =
    retro. ADR 0009's ">500 ms button hold = retro" is not implementable —
    the documented long-press slot is only a 1 s hold released before 2 s,
    and holds ≥2 s are firmware-reserved (2 s deep sleep, 5 s pairing window,
    15 s ship mode), so the report recommends double-tap instead. The
    `Glasses` Protocol returns a plain bool, so the retro distinction is
    surfaced only via `self.last_trigger_kind` ("single" | "retro") for
    future pipeline use.

    Parameters
    ----------
    quality : str
        Capture quality, one of VERY_HIGH/HIGH/MEDIUM/LOW (~80/47/25/16 KB
        JPEG — inspection §7.11). Default MEDIUM: ~25 KB keeps the BLE
        transfer time sane at MTU-sized chunks.
        TODO(hardware): the firmware's own default is undocumented; confirm
        MEDIUM is a sensible default for real capture latency.
    resolution : int
        Capture resolution. Only 640 is supported today (inspection §7.11 —
        do not assume Frame-like 1280x720); any other value raises.
    trigger_timeout_s : float | None
        `wait_for_trigger()` returns False after this many seconds without a
        tap. None (default) waits indefinitely (disconnect still yields
        False).
    capture_timeout_s : float
        Max seconds to wait for a complete JPEG in `capture_image()`.
    """

    def __init__(
        self,
        quality: str = "MEDIUM",
        resolution: int = 640,
        trigger_timeout_s: float | None = None,
        capture_timeout_s: float = 30.0,
    ) -> None:
        if quality not in QUALITY_LEVELS:
            raise ValueError(f"quality must be one of {QUALITY_LEVELS}, got {quality!r}")
        if resolution != 640:
            raise ValueError(
                "Halo supports only resolution=640 today (inspection §7.11)."
            )
        self.quality = quality
        self.resolution = resolution
        self.trigger_timeout_s = trigger_timeout_s
        self.capture_timeout_s = capture_timeout_s
        # Which gesture fired the last trigger: "single" | "retro" | None.
        # This is a HaloGlasses implementation detail — it is NOT part of the
        # `Glasses` Protocol (`src/compass/glasses/base.py`), and no pipeline
        # code reads it (`run_visual`/`run_verbal`/`run_retro` in
        # `src/compass/pipeline.py` select their mode at launch via `--mode`).
        # It is reserved for future unified-mode work, where one running app
        # would serve all three modes and need the gesture-to-mode mapping;
        # see ADR 0009's "trigger vocabulary deferred" postscript
        # (`docs/decisions/0009-halo-language-strategy.md`) for why the
        # Protocol is not being widened to carry it yet.
        self.last_trigger_kind: str | None = None

        self._msg: Any = None            # brilliant_msg.BrilliantMsg once connected
        self._tap_queue: Any = None      # asyncio.Queue from RxTap.attach()
        self._photo_queue: Any = None    # asyncio.Queue from RxPhoto.attach()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._loop_thread: threading.Thread | None = None

    # ---- lifecycle ---------------------------------------------------------

    def connect(self) -> None:
        """Connect over BLE, upload halo.lua as the frame app, and start it.

        First-time pairing is a physical act on the device (5 s button hold
        opens a ~60 s window — inspection §PAIRING 3.2/3.3); afterwards a
        bonded host reconnects freely but is refused while another bonded
        host holds the link. Out of the box (zero bonds) Halo is always
        pairable.
        """
        # Deferred heavy import, mirroring WhisperSTT.__init__'s deferral of
        # faster_whisper: the module imports (and tests instantiate) cleanly
        # without the SDK installed.
        try:
            import brilliant_msg  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "HaloGlasses.connect() requires the Halo SDK. "
                "Install with: pip install brilliant-msg — deliberately NOT in "
                "the project extras until hardware arrives (ADR 0009)."
            ) from exc

        # Documented import path: `from brilliant_msg import BrilliantMsg, ...`
        # (msg README example).
        # TODO(hardware): RxPhoto/RxTap are documented classes (msg CHANGELOG)
        # but their import path is unverified — assumed flat like TxSprite.
        from brilliant_msg import BrilliantMsg, RxPhoto, RxTap

        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(
            target=self._loop.run_forever, name="halo-ble-loop", daemon=True
        )
        self._loop_thread.start()

        async def _connect_async() -> None:
            self._msg = BrilliantMsg()
            await self._msg.connect()  # per msg README example
            # Upload our reflex app and start it — the documented host-side
            # flow (msg README: upload_frame_app -> start_frame_app). Under
            # the hood this is the REPL-channel file write + runtime restart
            # the inspection report documents (§7.3 frame.file.open, §3.1.2
            # control code 0x04).
            lua_path = Path(__file__).with_name("halo.lua")
            await self._msg.upload_frame_app(local_filename=str(lua_path))
            self._msg.attach_print_response_handler()  # per msg README example
            await self._msg.start_frame_app()
            # TODO(hardware): msg README also shows upload_stdlua_libs(
            # lib_names=['data', 'sprite']) before the frame app — halo.lua is
            # written against the raw frame.* API only (see its header), so no
            # std libs are uploaded here. If RxTap/RxPhoto turn out to require
            # their std-lib wire format, upload ['data', 'camera'] and adapt.
            #
            # TODO(hardware): Rx attach shape is frame-msg-lineage inference
            # (brilliant_sdk ships MIGRATION.md from frame-msg); the msg tests
            # document Rx classes "with handler dispatch functionality" but
            # not the public attach API. Assumed: attach() -> asyncio.Queue.
            self._tap_queue = await RxTap().attach(self._msg)
            self._photo_queue = await RxPhoto().attach(self._msg)

        try:
            self._run(_connect_async(), timeout=60.0)
        except BaseException:
            # Setup failed partway (e.g. BLE connected but the app upload or
            # Rx attach raised). The pipeline only enters its try/finally
            # after connect() returns, so nobody will call close() for us —
            # disconnect and release the loop thread here, then re-raise.
            self.close()
            raise

    def close(self) -> None:
        """Disconnect (plain BLE disconnect; advertising resumes — inspection
        §PAIRING 3.2) and release the private event loop."""
        if self._loop is None:
            return

        async def _close_async() -> None:
            if self._msg is not None:
                try:
                    self._msg.detach_print_response_handler()  # per msg README
                    await self._msg.stop_frame_app()           # per msg README
                finally:
                    await self._msg.disconnect()               # per msg README

        try:
            self._run(_close_async(), timeout=10.0)
        except Exception:
            pass  # tearing down anyway; BLE may already be gone
        finally:
            self._loop.call_soon_threadsafe(self._loop.stop)
            if self._loop_thread is not None:
                self._loop_thread.join(timeout=5.0)
            self._loop.close()
            self._loop = None
            self._loop_thread = None
            self._msg = None
            self._tap_queue = None
            self._photo_queue = None

    # ---- input -------------------------------------------------------------

    def wait_for_trigger(self) -> bool:
        """Block until a tap event arrives from halo.lua.

        Single tap (button or IMU — inspection §7.4/§7.6) -> True, with
        `last_trigger_kind = "single"`. Double tap -> True with
        `last_trigger_kind = "retro"` (see class docstring for why not a
        button hold). Note the documented caveat that a single IMU tap is
        reported ~one gesture window late by design (§7.6).

        Returns False on trigger_timeout_s expiry or when the link drops.
        TODO(hardware): brilliant-msg's disconnect signalling is undocumented
        — assumed here to surface as an exception out of the queue await;
        verify and map explicitly.
        """
        assert self._msg is not None, "Call connect() first"

        async def _next_tap() -> Any:
            assert self._tap_queue is not None
            return await self._tap_queue.get()

        while True:
            try:
                tap = self._run(_next_tap(), timeout=self.trigger_timeout_s)
            except (concurrent.futures.TimeoutError, TimeoutError):
                return False
            except Exception:
                return False  # link dropped mid-wait
            # Halo sends native tap kinds 'single'/'double'/'triple' as
            # payload bytes (msg CHANGELOG 7.1.0); RxTap delivers the kind.
            # TODO(hardware): confirm whether RxTap yields str or bytes.
            kind = tap.decode() if isinstance(tap, bytes) else str(tap)
            if kind == "single":
                self.last_trigger_kind = "single"
                return True
            if kind == "double":
                self.last_trigger_kind = "retro"
                return True
            # 'triple' (and anything else) is unassigned — keep waiting.

    # ---- capture -----------------------------------------------------------

    def capture_image(self) -> bytes:
        """Request a capture from halo.lua and return the complete JPEG.

        Flow (inspection §7.11): halo.lua wakes the camera
        (camera.power_save(false)), captures at the requested quality,
        polls image_ready(), then relays complete JPEG data in MTU-sized
        chunks over the data channel (§7.5); RxPhoto assembles them
        host-side (msg CHANGELOG: "photo capture from camera").
        """
        assert self._msg is not None, "Call connect() first"

        async def _capture_async() -> bytes:
            assert self._photo_queue is not None
            # Quality index into QUALITY_LEVELS, one byte (compass-defined
            # payload; halo.lua maps it back to the §7.11 quality string).
            payload = bytes([QUALITY_LEVELS.index(self.quality)])
            await self._msg.send_message(MSG_CAPTURE, payload)  # per msg README
            jpeg = await asyncio.wait_for(
                self._photo_queue.get(), timeout=self.capture_timeout_s
            )
            # TODO(hardware): confirm RxPhoto yields the assembled bytes
            # directly (vs. an object wrapping them) and that halo.lua's
            # end-of-image sentinel (see its pump_camera) matches what
            # RxPhoto treats as final-chunk.
            return bytes(jpeg)

        return self._run(_capture_async(), timeout=self.capture_timeout_s + 5.0)

    # ---- display -----------------------------------------------------------

    def show_text(self, line1: str, line2: str = "", color: str = "white") -> None:
        """Render up to two lines on the HUD via halo.lua.

        Colors map compass names to 24-bit RGB — Halo's display.text takes
        0xRRGGBB per call (inspection §7.10; a 16-entry palette exists
        internally but text() takes RGB directly). Unknown names fall back
        to white, like MockGlasses. Truncation: 28 chars line1 / 30 chars
        line2 (Dogica 8px = 30 chars/line on Halo, msg CHANGELOG 7.1.0);
        MockGlasses clips at the same widths.
        """
        assert self._msg is not None, "Call connect() first"
        rgb = COLORS.get(color, COLORS["white"])
        line1 = (line1 or "")[:LINE1_MAX]
        line2 = (line2 or "")[:LINE2_MAX]
        # Compass-defined payload: "RRGGBB\nline1\nline2" — parsed by
        # halo.lua's on_data. Small enough to fit one MTU chunk (<=512,
        # inspection §3.1); multi-chunk reassembly of host->device user data
        # would be the app's job (§2.1) and is deliberately not needed here.
        payload = f"{rgb:06X}\n{line1}\n{line2}".encode()

        async def _send() -> None:
            await self._msg.send_message(MSG_TEXT, payload)  # per msg README

        self._run(_send(), timeout=10.0)

    # ---- helpers -----------------------------------------------------------

    def _run(self, coro: Any, timeout: float | None) -> Any:
        """Bridge one coroutine onto the private loop and wait synchronously."""
        assert self._loop is not None, "Call connect() first"
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        try:
            return future.result(timeout=timeout)
        except BaseException:
            future.cancel()
            raise
