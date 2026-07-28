"""Base LLM provider interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Message:
    role: str  # "user" | "assistant" | "system"
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    metadata: dict = field(default_factory=dict)


class BaseProvider(ABC):
    """Common interface every LLM provider must implement."""

    name: str = "base"

    @abstractmethod
    def chat(
        self,
        messages: list[Message],
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs,
    ) -> LLMResponse:
        """Send a chat request and return a structured response."""

    @abstractmethod
    def list_models(self) -> list[str]:
        """Return available model identifiers for this provider."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the provider is configured and reachable."""
