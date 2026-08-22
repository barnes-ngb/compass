"""Mock Glasses — laptop webcam + an OpenCV window simulating a 640x400
right-eye micro-OLED HUD.

This lets us build and test the whole pipeline without real glasses. When
Phase 1 hardware arrives, only the driver behind the `Glasses` protocol
changes — `compass.cli` flips `GLASSES=frame` and the rest works unchanged.
"""

from __future__ import annotations

import cv2
import numpy as np

# Frame's actual display resolution. Other devices have different sizes, but
# 640x400 is a reasonable common simulator target.
HUD_W, HUD_H = 640, 400

PALETTE = {
    "void":      (28, 16, 16),
    "white":     (240, 240, 240),
    "grey":      (160, 160, 160),
    "red":       (60, 40, 230),
    "green":     (80, 220, 80),
    "yellow":    (40, 220, 230),
    "cloudblue": (220, 200, 120),
}


class MockGlasses:
    PREVIEW_WIN = "Camera Preview"
    HUD_WIN = "HUD (Compass Simulator)"

    def __init__(self, camera_index: int = 0) -> None:
        self._camera_index = camera_index
        self._cap: cv2.VideoCapture | None = None
        self._last_frame: np.ndarray | None = None
        self._hud_canvas: np.ndarray = self._blank_hud()

    # ---- lifecycle ---------------------------------------------------------

    def connect(self) -> None:
        # CAP_DSHOW gives faster, more reliable webcam open on Windows.
        self._cap = cv2.VideoCapture(self._camera_index, cv2.CAP_DSHOW)
        if not self._cap.isOpened():
            raise RuntimeError(
                f"Could not open camera at index {self._camera_index}. "
                "Close any app holding the webcam (Teams/Zoom/OBS) or try CAMERA_INDEX=1."
            )
        cv2.namedWindow(self.PREVIEW_WIN, cv2.WINDOW_NORMAL)
        cv2.namedWindow(self.HUD_WIN, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.HUD_WIN, HUD_W, HUD_H)
        self.show_text("Compass", "SPACE = capture / ESC = quit", color="cloudblue")

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        cv2.destroyAllWindows()

    # ---- input -------------------------------------------------------------

    def wait_for_trigger(self) -> bool:
        assert self._cap is not None, "Call connect() first"
        while True:
            ok, frame = self._cap.read()
            if not ok:
                self.show_text("Camera read failed", "Retrying...", color="red")
                continue
            self._last_frame = frame
            cv2.imshow(self.PREVIEW_WIN, frame)
            cv2.imshow(self.HUD_WIN, self._hud_canvas)
            key = cv2.waitKey(15) & 0xFF
            if key == 27:        # ESC
                return False
            if key == 32:        # SPACE
                return True
            if cv2.getWindowProperty(self.PREVIEW_WIN, cv2.WND_PROP_VISIBLE) < 1:
                return False
            if cv2.getWindowProperty(self.HUD_WIN, cv2.WND_PROP_VISIBLE) < 1:
                return False

    # ---- capture -----------------------------------------------------------

    def capture_image(self) -> bytes:
        if self._last_frame is None:
            assert self._cap is not None
            ok, frame = self._cap.read()
            if not ok:
                raise RuntimeError("Failed to capture an image from the webcam.")
            self._last_frame = frame
        ok, buf = cv2.imencode(".jpg", self._last_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ok:
            raise RuntimeError("Failed to encode JPEG.")
        return bytes(buf)

    # ---- display -----------------------------------------------------------

    def show_text(self, line1: str, line2: str = "", color: str = "white") -> None:
        self._hud_canvas = self._render_hud(line1, line2, color)
        cv2.imshow(self.HUD_WIN, self._hud_canvas)
        cv2.waitKey(1)

    # ---- helpers -----------------------------------------------------------

    @staticmethod
    def _blank_hud() -> np.ndarray:
        canvas = np.zeros((HUD_H, HUD_W, 3), dtype=np.uint8)
        canvas[:] = PALETTE["void"]
        return canvas

    @classmethod
    def _render_hud(cls, line1: str, line2: str, color: str) -> np.ndarray:
        canvas = cls._blank_hud()
        bgr = PALETTE.get(color, PALETTE["white"])
        # Truncation matches HaloGlasses (halo.py LINE1_MAX/LINE2_MAX): Halo
        # renders Dogica 8px at 30 chars/line, so line2 clips at 30, not the
        # 32 this simulator used to allow. The simulator must never be more
        # generous than the hardware — text tuned here would otherwise clip
        # on the device, and nobody would find out until wearing it.
        line1 = (line1 or "")[:28]
        line2 = (line2 or "")[:30]
        font = cv2.FONT_HERSHEY_DUPLEX
        cls._draw_centered(
            canvas, line1, y=HUD_H // 2 - 20, font=font, scale=1.1, color=bgr, thickness=2
        )
        if line2:
            cls._draw_centered(
                canvas, line2, y=HUD_H // 2 + 30, font=font, scale=0.6,
                color=PALETTE["grey"], thickness=1,
            )
        return canvas

    @staticmethod
    def _draw_centered(canvas, text, *, y, font, scale, color, thickness) -> None:
        (tw, _th), _baseline = cv2.getTextSize(text, font, scale, thickness)
        x = max(10, (canvas.shape[1] - tw) // 2)
        cv2.putText(canvas, text, (x, y), font, scale, color, thickness, cv2.LINE_AA)
