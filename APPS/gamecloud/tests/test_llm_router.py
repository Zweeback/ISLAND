"""Tests for LLM router and providers."""
from unittest.mock import MagicMock, patch

import pytest

from src.llm.base import LLMResponse, Message
from src.llm.router import LLMRouter


# ── Helpers ──────────────────────────────────────────────────────────────────


def _mock_response(content="hello", provider="openai", model="gpt-4o-mini"):
    return LLMResponse(
        content=content, model=model, provider=provider, input_tokens=5, output_tokens=3
    )


# ── Router tests ─────────────────────────────────────────────────────────────


def test_router_init_creates_all_providers():
    router = LLMRouter()
    assert set(router._providers) == {"openai", "anthropic", "gemini", "ollama"}


def test_router_get_provider_unknown_raises():
    router = LLMRouter()
    with pytest.raises(ValueError, match="Unknown provider"):
        router.get_provider("nonexistent")


def test_router_available_providers_empty_without_keys(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("OLLAMA_HOST", "http://unreachable:11434")
    router = LLMRouter()
    available = router.available_providers()
    # openai/anthropic/gemini require keys; ollama requires a reachable host
    assert "openai" not in available
    assert "anthropic" not in available
    assert "gemini" not in available


def test_router_chat_delegates_to_provider(monkeypatch):
    router = LLMRouter()
    mock_provider = MagicMock()
    mock_provider.name = "openai"
    mock_provider.chat.return_value = _mock_response()
    router._providers["openai"] = mock_provider

    msgs = [Message(role="user", content="hi")]
    resp = router.chat(msgs, provider="openai")
    mock_provider.chat.assert_called_once()
    assert resp.content == "hello"


def test_router_ask_convenience(monkeypatch):
    router = LLMRouter()
    mock_provider = MagicMock()
    mock_provider.name = "openai"
    mock_provider.chat.return_value = _mock_response(content="world")
    router._providers["openai"] = mock_provider

    result = router.ask("say something", provider="openai")
    assert result == "world"


def test_router_status_returns_per_provider_info():
    router = LLMRouter()
    status = router.status()
    assert set(status) == {"openai", "anthropic", "gemini", "ollama"}
    for info in status.values():
        assert "available" in info
        assert "models" in info


def test_router_register_custom_provider():
    router = LLMRouter()
    custom = MagicMock()
    custom.name = "my_custom_llm"
    router.register(custom)
    assert "my_custom_llm" in router._providers
