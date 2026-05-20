"""Google Gemini vision provider — STUB.

When ready:
1.  Uncomment `google-generativeai` in requirements.txt.
2.  Implement `describe()` with google.generativeai.GenerativeModel("gemini-2.5-flash").

Gemini Flash is cheaper than Claude Sonnet for high-volume cases. Same
VisionProvider interface, drop-in swap.
"""

from __future__ import annotations


class GeminiVision:
    def __init__(self, api_key: str) -> None:
        raise NotImplementedError(
            "GeminiVision is a stub. Use VISION_PROVIDER=claude or "
            "VISION_PROVIDER=mock until this is implemented."
        )

    def describe(self, image_jpeg: bytes, prompt: str) -> str: ...
