"""Google Gemini provider (Gemini 1.5 Pro, Flash, …)."""
from __future__ import annotations

import os

from src.llm.base import BaseProvider, LLMResponse, Message

_DEFAULT_MODEL = "gemini-1.5-flash"
_MODELS = [
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-2.0-flash-exp",
]


class GeminiProvider(BaseProvider):
    name = "gemini"

    def __init__(self, api_key: str | None = None, default_model: str = _DEFAULT_MODEL):
        self._api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self.default_model = default_model

    def _client(self):
        try:
            import google.generativeai as genai

            genai.configure(api_key=self._api_key)
            return genai
        except ImportError as exc:
            raise RuntimeError("google-generativeai package not installed") from exc

    def chat(
        self,
        messages: list[Message],
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs,
    ) -> LLMResponse:
        genai = self._client()
        model_name = model or self.default_model

        system_parts = [m.content for m in messages if m.role == "system"]
        history = []
        last_user: str | None = None

        for m in messages:
            if m.role == "system":
                continue
            if m.role == "user":
                last_user = m.content
                history.append({"role": "user", "parts": [m.content]})
            elif m.role == "assistant":
                history.append({"role": "model", "parts": [m.content]})

        gen_model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction="\n\n".join(system_parts) if system_parts else None,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            ),
        )

        prompt = last_user or ""
        chat_session = gen_model.start_chat(history=history[:-1] if history else [])
        response = chat_session.send_message(prompt)

        usage = response.usage_metadata
        return LLMResponse(
            content=response.text,
            model=model_name,
            provider=self.name,
            input_tokens=getattr(usage, "prompt_token_count", 0),
            output_tokens=getattr(usage, "candidates_token_count", 0),
        )

    def list_models(self) -> list[str]:
        return list(_MODELS)

    def is_available(self) -> bool:
        return bool(self._api_key)
