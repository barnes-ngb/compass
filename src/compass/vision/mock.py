"""Mock vision provider — canned answers for offline iteration."""

from __future__ import annotations

import itertools


class MockVision:
    def __init__(self) -> None:
        self._answers = itertools.cycle([
            "Eastern red cedar tree",
            "Common house sparrow",
            "Black-capped chickadee",
            "Red oak leaf",
            "Eastern grey squirrel",
            "Sugar maple seedling",
            "Mourning dove",
        ])

    def describe(self, image_jpeg: bytes, prompt: str) -> str:  # noqa: ARG002
        return next(self._answers)
