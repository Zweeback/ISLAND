#!/usr/bin/env python3
"""Fail-closed multi-LLM router for GitHub Actions.

Default provider order uses only services that can operate without a payment
method: GitHub Models included quota, Gemini API free tier, and an optional
user-controlled OpenAI-compatible endpoint.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from typing import Callable


@dataclass
class Attempt:
    provider: str
    ok: bool
    status: int | None
    category: str
    message: str
    elapsed_ms: int


class ProviderError(RuntimeError):
    def __init__(self, category: str, message: str, status: int | None = None):
        super().__init__(message)
        self.category = category
        self.status = status


def post_json(url: str, payload: dict, headers: dict[str, str], timeout: int = 90) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:1000]
        if exc.code == 429:
            category = "quota_exhausted"
        elif exc.code in (401, 403):
            category = "auth"
        elif 500 <= exc.code <= 599:
            category = "transient"
        else:
            category = "request"
        raise ProviderError(category, f"HTTP {exc.code}: {body}", exc.code) from exc
    except urllib.error.URLError as exc:
        raise ProviderError("network", str(exc.reason)) from exc
    except TimeoutError as exc:
        raise ProviderError("timeout", str(exc)) from exc


def github_models(prompt: str) -> str:
    token = os.getenv("GITHUB_MODELS_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        raise ProviderError("unavailable", "GITHUB_MODELS_TOKEN is not set")
    model = os.getenv("GITHUB_MODEL", "openai/gpt-4.1")
    result = post_json(
        "https://models.github.ai/inference/chat/completions",
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": int(os.getenv("MAX_OUTPUT_TOKENS", "1600")),
        },
        {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
            "Content-Type": "application/json",
        },
    )
    return result["choices"][0]["message"]["content"]


def gemini(prompt: str) -> str:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ProviderError("unavailable", "GEMINI_API_KEY is not set")
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    encoded_model = urllib.parse.quote(model, safe="-._")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{encoded_model}:generateContent?key={urllib.parse.quote(key, safe='')}"
    )
    result = post_json(
        url,
        {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": int(os.getenv("MAX_OUTPUT_TOKENS", "1600")),
            },
        },
        {"Content-Type": "application/json"},
    )
    candidates = result.get("candidates") or []
    if not candidates:
        raise ProviderError("empty_response", json.dumps(result)[:1000])
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts).strip()
    if not text:
        raise ProviderError("empty_response", "Gemini returned no text")
    return text


def custom_openai(prompt: str) -> str:
    base = os.getenv("CUSTOM_LLM_BASE_URL", "").rstrip("/")
    if not base:
        raise ProviderError("unavailable", "CUSTOM_LLM_BASE_URL is not set")
    key = os.getenv("CUSTOM_LLM_API_KEY", "")
    model = os.getenv("CUSTOM_LLM_MODEL", "default")
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    result = post_json(
        f"{base}/chat/completions",
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": int(os.getenv("MAX_OUTPUT_TOKENS", "1600")),
        },
        headers,
    )
    return result["choices"][0]["message"]["content"]


def paid_openai_compatible(prompt: str, provider: str) -> str:
    if os.getenv("ALLOW_PAID_PROVIDERS", "false").lower() != "true":
        raise ProviderError("blocked", f"{provider} is disabled by FREE_ONLY policy")
    if provider == "openai":
        base, key_var, model_var, default_model = (
            "https://api.openai.com/v1",
            "OPENAI_API_KEY",
            "OPENAI_MODEL",
            "gpt-5.6-luna",
        )
    else:
        base, key_var, model_var, default_model = (
            "https://api.x.ai/v1",
            "XAI_API_KEY",
            "XAI_MODEL",
            "grok-4.5",
        )
    key = os.getenv(key_var)
    if not key:
        raise ProviderError("unavailable", f"{key_var} is not set")
    result = post_json(
        f"{base}/chat/completions",
        {
            "model": os.getenv(model_var, default_model),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": int(os.getenv("MAX_OUTPUT_TOKENS", "1600")),
        },
        {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    return result["choices"][0]["message"]["content"]


PROVIDERS: dict[str, Callable[[str], str]] = {
    "github": github_models,
    "gemini": gemini,
    "custom": custom_openai,
    "openai": lambda prompt: paid_openai_compatible(prompt, "openai"),
    "xai": lambda prompt: paid_openai_compatible(prompt, "xai"),
}


def run(prompt: str, order: list[str]) -> tuple[str, str, list[Attempt]]:
    attempts: list[Attempt] = []
    retry_delay = float(os.getenv("TRANSIENT_RETRY_DELAY_SECONDS", "2"))

    for name in order:
        provider = PROVIDERS.get(name)
        if provider is None:
            attempts.append(Attempt(name, False, None, "unknown", "Unknown provider", 0))
            continue

        started = time.monotonic()
        try:
            text = provider(prompt)
            elapsed = int((time.monotonic() - started) * 1000)
            attempts.append(Attempt(name, True, 200, "success", "ok", elapsed))
            return name, text, attempts
        except ProviderError as exc:
            elapsed = int((time.monotonic() - started) * 1000)
            attempts.append(Attempt(name, False, exc.status, exc.category, str(exc), elapsed))
            if exc.category in {"transient", "network", "timeout"}:
                time.sleep(retry_delay)
        except Exception as exc:  # defensive boundary between providers
            elapsed = int((time.monotonic() - started) * 1000)
            attempts.append(Attempt(name, False, None, "internal", repr(exc), elapsed))

    raise ProviderError("all_failed", json.dumps([asdict(a) for a in attempts]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument(
        "--providers",
        default=os.getenv("PROVIDER_ORDER", "github,gemini,custom"),
        help="Comma-separated fallback order",
    )
    parser.add_argument("--output", default="cloud_runner_result.json")
    args = parser.parse_args()

    order = [item.strip().lower() for item in args.providers.split(",") if item.strip()]
    try:
        provider, text, attempts = run(args.prompt, order)
        result = {
            "ok": True,
            "provider": provider,
            "response": text,
            "attempts": [asdict(a) for a in attempts],
            "free_only": os.getenv("ALLOW_PAID_PROVIDERS", "false").lower() != "true",
        }
        exit_code = 0
    except ProviderError as exc:
        result = {
            "ok": False,
            "category": exc.category,
            "error": str(exc),
            "free_only": os.getenv("ALLOW_PAID_PROVIDERS", "false").lower() != "true",
        }
        exit_code = 1

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
