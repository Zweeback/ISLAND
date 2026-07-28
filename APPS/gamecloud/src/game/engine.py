"""
GameCloud Engine – minimal scaffold for an LLM-assisted cloud game loop.

Each game session has:
- A world state dictionary updated each turn.
- An LLM-backed narrator / AI opponent.
- Pluggable rules functions.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from src.llm.router import LLMRouter
from src.llm.providers import Message


@dataclass
class GameSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: dict[str, Any] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)


class GameEngine:
    """
    Minimal game loop that uses an LLMRouter for AI narration/logic.

    Quick start::

        engine = GameEngine()
        session = engine.new_session({"scene": "forest", "hp": 100})
        response = engine.step(session, "I look around.")
        print(response)
    """

    NARRATOR_SYSTEM = (
        "You are the narrator of a cloud-based text adventure game. "
        "Describe the world vividly, respond to player actions, and advance "
        "the story. Keep responses concise (≤150 words). "
        "Current world state will be provided as JSON."
    )

    def __init__(
        self,
        router: LLMRouter | None = None,
        provider: str | None = None,
        model: str | None = None,
        rules: list[Callable[[GameSession, str], str | None]] | None = None,
    ) -> None:
        self.router = router or LLMRouter()
        self.provider = provider
        self.model = model
        self.rules: list[Callable] = rules or []

    # ── Session management ────────────────────────────────────────────────

    def new_session(self, initial_state: dict | None = None) -> GameSession:
        session = GameSession(state=initial_state or {})
        return session

    # ── Game step ─────────────────────────────────────────────────────────

    def step(self, session: GameSession, player_input: str) -> str:
        """Process one player turn and return the narrator's response."""
        # Run pre-step rules (e.g. damage, inventory checks)
        for rule in self.rules:
            override = rule(session, player_input)
            if override is not None:
                session.history.append(f"[rule] {override}")
                return override

        import json

        state_json = json.dumps(session.state, ensure_ascii=False, indent=2)
        messages: list[Message] = [
            Message(role="system", content=self.NARRATOR_SYSTEM),
            Message(
                role="user",
                content=f"World state:\n{state_json}\n\nPlayer: {player_input}",
            ),
        ]
        # Include recent history as context
        for past in session.history[-6:]:
            messages.append(Message(role="assistant", content=past))
        # Re-add the current player message at the end
        messages.append(
            Message(
                role="user",
                content=f"World state:\n{state_json}\n\nPlayer: {player_input}",
            )
        )

        response = self.router.chat(
            messages=messages,
            provider=self.provider,
            model=self.model,
        )
        session.history.append(response.content)
        return response.content
