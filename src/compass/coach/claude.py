"""Claude-backed coach.

Synthesizes intent + transcript + memory context into a short HUD directive.
The system prompt nudges Claude to be brief, glanceable, and honest about
uncertainty.
"""

from __future__ import annotations

from anthropic import Anthropic

SYSTEM_PROMPT = """You are Compass, a glance-paced assistant that appears in
the wearer's right eye as 1-2 short lines of text.

Constraints:
- Be brief. 8 words or fewer when possible. Never more than 2 lines.
- Be specific. Names, numbers, decisions — not vibes.
- If the transcript doesn't contain the answer, say "not in last buffer"
  rather than guess.
- No greetings, no sign-offs, no apologies.
- If asked for a summary, give the through-line, not a recap.
"""


class ClaudeCoach:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6") -> None:
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set. Add it to .env or set "
                "COACH_PROVIDER=mock to run offline."
            )
        self._client = Anthropic(api_key=api_key)
        self._model = model

    def respond(self, intent: str, transcript: str, memory_context: str = "") -> str:
        parts = [f"Intent: {intent}"]
        if memory_context:
            parts.append(f"\nRelevant memory:\n{memory_context}")
        if transcript:
            parts.append(f"\nRecent transcript:\n{transcript}")
        user_msg = "\n".join(parts)

        message = self._client.messages.create(
            model=self._model,
            max_tokens=64,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        text = "".join(
            block.text for block in message.content if getattr(block, "type", None) == "text"
        )
        return text.strip()
