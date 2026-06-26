from __future__ import annotations
import json
import urllib.request
import sys


def call_xai(api_key: str, model: str, system_prompt: str, user_prompt: str) -> str:
    """
    Direct HTTP request to xAI Chat Completions API using urllib.
    Requires no external packages. Returns JSON text or error string.
    """
    url = "https://api.x.ai/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    # Map "eve" to grok-beta (or grok-4 if that's what xAI goes by)
    # The user mentioned grok-4 or grok-beta. They likely just provisioned the key
    # and have no credits/access yet (which results in "Model not found" or
    # "permission-denied" errors right now).
    # We will trust their requested model string "grok-beta" as requested.
    actual_model = model
    if model.lower() == "eve":
        actual_model = "grok-beta"
    elif model.lower() == "grok-4":
        actual_model = "grok-beta"  # mapping to current known endpoint just in case

    # xAI API is very similar to OpenAI's
    payload = {
        "model": actual_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            raw_data = response.read().decode("utf-8")
            res_data = json.loads(raw_data)
            choices = res_data.get("choices", [])
            if choices and isinstance(choices, list) and len(choices) > 0:
                first_choice = choices[0]
                if isinstance(first_choice, dict):
                    message = first_choice.get("message", {})
                    if isinstance(message, dict):
                        content = message.get("content", "")
                        return str(content)
            return json.dumps({"error": "Unexpected xAI response format"})
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode("utf-8")
        print(f"xAI API HTTP Error {e.code}: {error_msg}", file=sys.stderr)
        return json.dumps({"error": f"xAI Call failed with {e.code}: {error_msg}"})
    except Exception as e:
        print(f"xAI API Call failed: {e}", file=sys.stderr)
        return json.dumps({"error": f"xAI Call failed: {e}"})
