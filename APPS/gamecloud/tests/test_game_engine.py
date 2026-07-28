"""Tests for the GameCloud Engine."""
from unittest.mock import MagicMock

import pytest

from src.game.engine import GameEngine, GameSession
from src.llm.base import LLMResponse


def _mock_router(content="You see a dark forest ahead."):
    router = MagicMock()
    router.chat.return_value = LLMResponse(
        content=content, model="gpt-4o-mini", provider="openai"
    )
    return router


def test_new_session_has_unique_ids():
    engine = GameEngine(router=_mock_router())
    s1 = engine.new_session()
    s2 = engine.new_session()
    assert s1.session_id != s2.session_id


def test_new_session_stores_initial_state():
    engine = GameEngine(router=_mock_router())
    session = engine.new_session({"hp": 100, "scene": "town"})
    assert session.state["hp"] == 100
    assert session.state["scene"] == "town"


def test_step_appends_to_history():
    router = _mock_router("Narrator reply")
    engine = GameEngine(router=router)
    session = engine.new_session()
    resp = engine.step(session, "look around")
    assert resp == "Narrator reply"
    assert "Narrator reply" in session.history


def test_step_calls_router_chat():
    router = _mock_router()
    engine = GameEngine(router=router)
    session = engine.new_session()
    engine.step(session, "go north")
    router.chat.assert_called_once()


def test_rule_can_override_llm_response():
    router = _mock_router()
    engine = GameEngine(
        router=router,
        rules=[lambda session, inp: "You died." if "die" in inp else None],
    )
    session = engine.new_session()
    resp = engine.step(session, "please die")
    assert resp == "You died."
    # LLM should NOT have been called
    router.chat.assert_not_called()


def test_step_multiple_turns_builds_history():
    router = _mock_router("response")
    engine = GameEngine(router=router)
    session = engine.new_session()
    engine.step(session, "turn 1")
    engine.step(session, "turn 2")
    assert len(session.history) == 2
