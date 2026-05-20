"""Real Brilliant Labs Frame driver — STUB for Phase 1.

When real hardware arrives:
1.  Uncomment `frame-ble` and `frame-msg` in requirements.txt.
2.  Implement the bodies below using `frame_msg` (async; wrap with
    asyncio.run inside each method to keep the Glasses Protocol sync).

The Glasses Protocol was designed so that *only this file* changes when
swapping to real hardware. The rest of the pipeline doesn't care.

Reference SDK calls (see docs/landscape.md for hardware-availability notes):
    - frame.connect()                            BLE connect
    - frame.motion.wait_for_tap()                gesture trigger
    - frame.camera.save_photo(...)               JPEG capture
    - frame.display.show_text(text, align=...)   render line
"""

from __future__ import annotations


class FrameGlasses:
    def __init__(self) -> None:
        raise NotImplementedError(
            "FrameGlasses is a Phase 1 stub. Set GLASSES=mock in .env. "
            "See docs/decisions/0004-hardware-strategy.md for what to buy "
            "(short version: used Frame on eBay, or Vuzix Z100 + M400)."
        )

    def connect(self) -> None: ...
    def wait_for_trigger(self) -> bool: ...
    def capture_image(self) -> bytes: ...
    def show_text(self, line1: str, line2: str = "", color: str = "white") -> None: ...
    def close(self) -> None: ...
