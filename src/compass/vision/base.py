"""The `VisionProvider` interface.

A provider takes JPEG bytes and a prompt, returns a short string. The
implementation can route to Claude, Gemini, a local Moondream, or canned mock
data — the pipeline can't tell the difference.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class VisionProvider(Protocol):
    def describe(self, image_jpeg: bytes, prompt: str) -> str:
        """Return a short natural-language answer about the image.

        Implementations should keep the answer short enough to fit a HUD
        (typically ≤8 words, ≤32 chars). The constraint is in the prompt —
        don't hard-code it here.
        """
        ...
