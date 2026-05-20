"""The `Glasses` interface.

Every glasses driver (mock webcam, real Frame, later Halo / Z100 / Ray-Ban
Display) must implement these primitives. That's all the pipeline needs.

Why a Protocol and not an ABC: structural typing means mock and real drivers
don't need a common ancestor, and third-party drivers can be dropped in
without inheriting from us.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Glasses(Protocol):
    """Contract for any pair of smart glasses (or a simulator)."""

    def connect(self) -> None:
        """Open the camera and the display. Called once at start."""
        ...

    def wait_for_trigger(self) -> bool:
        """Block until the user signals 'capture now'.

        Returns True if a capture was requested, False if the user
        wants to quit. Mock implementation maps SPACE → True, ESC → False.
        On real Frame this will map to a tap gesture.
        """
        ...

    def capture_image(self) -> bytes:
        """Capture one JPEG frame and return its bytes."""
        ...

    def show_text(self, line1: str, line2: str = "", color: str = "white") -> None:
        """Render up to two short lines on the HUD.

        Frame's display is small (640x400, 16-color palette). Keep lines
        ~28 characters each. The driver is allowed to truncate.
        """
        ...

    def close(self) -> None:
        """Release the camera and tear down the display."""
        ...
