"""OpenAI provider (GPT-4o, GPT-4, GPT-3.5-turbo, o1, …)."""
from __future__ import annotations

import os

from src.llm.base import BaseProvider, LLMResponse, Message

_DEFAULT_MODEL = "gpt-4o-mini"
_MODELS = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo", "o1-mini", "o1"]


class OpenAIProvider(BaseProvider):
    name = "openai"

    def __init__(self, api_key: str | None = None, default_model: str = _DEFAULT_MODEL):
        self._api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.default_model = default_model

    def _client(self):
        try:
            import openai

            return openai.OpenAI(api_key=self._api_key)
        except ImportError as exc:
            raise RuntimeError("openai package not installed") from exc

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
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )
        choice = response.choices[0]
        usage = response.usage or {}
        return LLMResponse(
            content=choice.message.content or "",
            model=model,
            provider=self.name,
            input_tokens=getattr(usage, "prompt_tokens", 0),
            output_tokens=getattr(usage, "completion_tokens", 0),
        )

    def list_models(self) -> list[str]:
        return list(_MODELS)

    def is_available(self) -> bool:
        return bool(self._api_key)
