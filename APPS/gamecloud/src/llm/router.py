"""LLM router – selects and delegates to the right provider."""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import BaseProvider

from .providers import (
    AnthropicProvider,
    BaseProvider,
    GeminiProvider,
    LLMResponse,
    Message,
    OllamaProvider,
    OpenAIProvider,
)

_PROVIDER_CLASSES: dict[str, type[BaseProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "ollama": OllamaProvider,
}


class LLMRouter:
    """
    Central router that manages multiple LLM providers and dispatches
    requests to the appropriate one.

    Usage::

        router = LLMRouter()
        response = router.chat(
            messages=[Message("user", "Hello!")],
            provider="openai",
            model="gpt-4o-mini",
        )
    """

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}
        self._default_provider: str = os.getenv(
            "GAMECLOUD_DEFAULT_PROVIDER", "openai"
        )
        self._default_model: str | None = os.getenv("GAMECLOUD_DEFAULT_MODEL")
        self._init_providers()

    # ── Provider lifecycle ────────────────────────────────────────────────

    def _init_providers(self) -> None:
        for name, cls in _PROVIDER_CLASSES.items():
            self._providers[name] = cls()

    def register(self, provider: BaseProvider) -> None:
        """Register a custom or additional provider instance."""
        self._providers[provider.name] = provider

    def available_providers(self) -> list[str]:
        """Return names of providers that are configured and reachable."""
        return [name for name, p in self._providers.items() if p.is_available()]

    def get_provider(self, name: str) -> BaseProvider:
        if name not in self._providers:
            raise ValueError(
                f"Unknown provider '{name}'. "
                f"Available: {list(self._providers)}"
            )
        return self._providers[name]

    # ── Chat ─────────────────────────────────────────────────────────────

    def chat(
        self,
        messages: list[Message],
        provider: str | None = None,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs,
    ) -> LLMResponse:
        """Route a chat request to the specified (or default) provider."""
        provider_name = provider or self._default_provider
        p = self.get_provider(provider_name)
        return p.chat(
            messages=messages,
            model=model or self._default_model,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )

    def ask(
        self,
        prompt: str,
        system: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        **kwargs,
    ) -> str:
        """Convenience wrapper: single prompt → response text."""
        messages: list[Message] = []
        if system:
            messages.append(Message(role="system", content=system))
        messages.append(Message(role="user", content=prompt))
        return self.chat(messages, provider=provider, model=model, **kwargs).content

    # ── Introspection ─────────────────────────────────────────────────────

    def status(self) -> dict[str, dict]:
        """Return availability and model list per provider."""
        return {
            name: {
                "available": p.is_available(),
                "models": p.list_models() if p.is_available() else [],
            }
            for name, p in self._providers.items()
        }
