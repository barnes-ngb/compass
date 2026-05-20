"""Mock coach — canned responses for offline iteration."""

from __future__ import annotations


class MockCoach:
    def respond(self, intent: str, transcript: str, memory_context: str = "") -> str:  # noqa: ARG002
        i = intent.lower()
        if "ask" in i:
            return "they asked about Q3 panel schedule"
        if "summar" in i:
            return "decided 16-ga steel, install Tuesday"
        if "decide" in i or "decis" in i:
            return "16-gauge weathering steel, Mon delivery"
        return "intent unclear"
