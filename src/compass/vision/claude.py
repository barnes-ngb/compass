"""Claude vision provider.

Uses the Anthropic Python SDK (>=0.40) with the base64-image content block
pattern. Verified against May 2026 docs at
https://docs.claude.com/en/docs/build-with-claude/vision

Cost note: at Sonnet 4.6 pricing (~$3/M input, $15/M output) a typical image
(~1500 tokens in, ~30 tokens out) costs roughly $0.005 per query. Haiku 4.5
is ~3x cheaper.
"""

from __future__ import annotations

import base64

from anthropic import Anthropic


class ClaudeVision:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6") -> None:
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set. Add it to .env or set "
                "VISION_PROVIDER=mock to run offline."
            )
        self._client = Anthropic(api_key=api_key)
        self._model = model

    def describe(self, image_jpeg: bytes, prompt: str) -> str:
        b64 = base64.standard_b64encode(image_jpeg).decode("ascii")
        message = self._client.messages.create(
            model=self._model,
            max_tokens=64,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": b64,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )
        text = "".join(
            block.text for block in message.content if getattr(block, "type", None) == "text"
        )
        return text.strip()
