"""The `CoachProvider` interface.

A coach takes a recent transcript, relevant memory context, and a user intent
("summarize", "what did they ask", "what did we decide") and returns a short
HUD directive.

The provider doesn't decide WHAT to recall — that's the memory layer's job.
The provider just synthesizes the inputs it receives.

This separation matters because retrieval policy will evolve faster than
synthesis quality. Today the memory layer hands the coach the last N
minutes of transcript. Tomorrow it might hand the coach a transcript + the
relevant session summaries + a daily digest. The coach stays the same.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class CoachProvider(Protocol):
    def respond(
        self,
        intent: str,
        transcript: str,
        memory_context: str = "",
    ) -> str:
        """Return a short HUD directive (≤8 words preferred).

        Args:
            intent: what the user is asking for. Free-text. Examples:
                "what did they just ask"
                "summarize the last 10 minutes"
                "what did we decide about steel grade"
            transcript: STT'd text of recent audio buffer or full session.
                May be empty for stateless verbal queries.
            memory_context: optional retrieved context from prior sessions
                or summaries. Empty for the simplest case.
        """
        ...
