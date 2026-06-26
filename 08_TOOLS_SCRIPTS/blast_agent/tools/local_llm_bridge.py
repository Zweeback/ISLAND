import json
import urllib.request
import urllib.parse
import sys


def query_ollama(system_prompt: str, user_prompt: str, model: str = "llama3") -> str:
    """
    Direct HTTP request to local Ollama API via /api/chat.
    """
    url = "http://localhost:11434/api/chat"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=120) as response:
            raw_data = response.read().decode("utf-8")
            res_data = json.loads(raw_data)

            message = res_data.get("message", {})
            if isinstance(message, dict):
                content = message.get("content", "")
                return str(content)

            return json.dumps({"error": "Unexpected Ollama response format"})
    except Exception as e:
        print(f"Ollama API Call failed: {e}", file=sys.stderr)
        return json.dumps({"error": f"Ollama Call failed: {e}"})

def get_installed_models() -> list[str]:
    """
    Get a list of models currently installed in the local Ollama instance.
    """
    url = "http://localhost:11434/api/tags"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as response:
            raw_data = response.read().decode("utf-8")
            res_data = json.loads(raw_data)
            models = []
            for m in res_data.get("models", []):
                if isinstance(m, dict) and "name" in m:
                    models.append(m["name"])
            return models
    except Exception as e:
        print(f"Failed to fetch Ollama models: {e}", file=sys.stderr)
        return []

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        print(json.dumps(get_installed_models()))
    else:
        print("Usage: python local_llm_bridge.py list", file=sys.stderr)
