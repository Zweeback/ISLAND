"""Ollama provider – local LLMs (Llama 3, Mistral, Phi-3, …)."""
from __future__ import annotations

import os

from src.llm.base import BaseProvider, LLMResponse, Message

_DEFAULT_MODEL = "llama3"


class OllamaProvider(BaseProvider):
    name = "ollama"

    def __init__(self, host: str | None = None, default_model: str = _DEFAULT_MODEL):
        self._host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.default_model = os.getenv("OLLAMA_DEFAULT_MODEL", default_model)

    def _client(self):
        try:
            import ollama

            return ollama.Client(host=self._host)
        except ImportError as exc:
            raise RuntimeError("ollama package not installed") from exc

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
        response = client.chat(
            model=model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            options={"num_predict": max_tokens, "temperature": temperature},
        )
        msg = response["message"]
        return LLMResponse(
            content=msg["content"],
            model=model,
            provider=self.name,
            input_tokens=response.get("prompt_eval_count", 0),
            output_tokens=response.get("eval_count", 0),
        )

    def list_models(self) -> list[str]:
        try:
            client = self._client()
            models = client.list()
            return [m["name"] for m in models.get("models", [])]
        except Exception:
            return [self.default_model]

    def is_available(self) -> bool:
        try:
            import httpx

            r = httpx.get(f"{self._host}/api/tags", timeout=2)
            return r.status_code == 200
        except Exception:
            return False
