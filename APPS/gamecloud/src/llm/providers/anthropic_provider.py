"""Anthropic provider (Claude 3.5 Sonnet, Claude 3 Opus, …)."""
from __future__ import annotations

import os

from src.llm.base import BaseProvider, LLMResponse, Message

_DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
_MODELS = [
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
]


class AnthropicProvider(BaseProvider):
    name = "anthropic"

    def __init__(self, api_key: str | None = None, default_model: str = _DEFAULT_MODEL):
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.default_model = default_model

    def _client(self):
        try:
            import anthropic

            return anthropic.Anthropic(api_key=self._api_key)
        except ImportError as exc:
            raise RuntimeError("anthropic package not installed") from exc

    def chat(
        self,
        messages: list[Message],
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs,
    ) -> LLMResponse:
        client = self._client()
        model = model or self.default_model

        # Anthropic separates system messages from the messages list.
        system_parts = [m.content for m in messages if m.role == "system"]
        chat_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role != "system"
        ]

        create_kwargs: dict = dict(
            model=model,
            max_tokens=max_tokens,
            messages=chat_messages,
            **kwargs,
        )
        if system_parts:
            create_kwargs["system"] = "\n\n".join(system_parts)

        response = client.messages.create(**create_kwargs)
        content = response.content[0].text if response.content else ""
        return LLMResponse(
            content=content,
            model=model,
            provider=self.name,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

    def list_models(self) -> list[str]:
        return list(_MODELS)

    def is_available(self) -> bool:
        return bool(self._api_key)
