# GameCloud – Multi-LLM Cloud Game Development Workspace

A blank-slate workspace for building cloud games powered by multiple LLM
providers. Opens instantly in **GitHub Codespaces** with everything pre-wired.

---

## What's included

| Layer | Contents |
|-------|----------|
| **Codespace** | `.devcontainer/devcontainer.json` – Python 3.11, Node 20, Docker-in-Docker, ports forwarded |
| **LLM providers** | OpenAI (GPT-4o), Anthropic (Claude 3.5), Google Gemini, Ollama (local) |
| **LLM router** | `src/llm/router.py` – unified `chat()` / `ask()` across all providers |
| **Game engine** | `src/game/engine.py` – session-based game loop with LLM narration |
| **REST API** | `src/main.py` – FastAPI server exposing chat + game endpoints |
| **Tests** | `tests/` – pytest suite with mocked providers |

---

## Quick start in Codespaces

1. Open in Codespace (the devcontainer installs all deps automatically).
2. Copy the env template and add your keys:
   ```bash
   cp .env.template .env
   # Edit .env – add OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.
   ```
3. Start the API:
   ```bash
   make run
   # → http://localhost:8000
   # → http://localhost:8000/docs  (Swagger UI)
   ```
4. Check provider status:
   ```bash
   make status
   ```

---

## API overview

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/status` | Provider health + model list |
| `POST` | `/chat` | Raw multi-LLM chat |
| `POST` | `/game/session` | Start a new game session |
| `POST` | `/game/{id}` | Take a game step |
| `GET`  | `/game/{id}` | Read session state + history |

### Example – raw chat

```http
POST /chat
{
  "messages": [{"role": "user", "content": "Hello!"}],
  "provider": "openai",
  "model": "gpt-4o-mini"
}
```

### Example – game session

```http
POST /game/session
{"initial_state": {"scene": "forest", "hp": 100}}

POST /game/{session_id}
{"player_input": "I look around carefully."}
```

---

## LLM providers

| Provider | Env key | Default model |
|----------|---------|---------------|
| OpenAI | `OPENAI_API_KEY` | `gpt-4o-mini` |
| Anthropic | `ANTHROPIC_API_KEY` | `claude-3-5-sonnet-20241022` |
| Google Gemini | `GOOGLE_API_KEY` | `gemini-1.5-flash` |
| Ollama (local) | `OLLAMA_HOST` | `llama3` |

All keys belong in `.env` (git-ignored). Never commit real keys.

---

## Development

```bash
make install   # pip install all deps
make test      # run pytest suite
make lint      # flake8
make run       # start API dev server on :8000
```

---

## Project structure

```
APPS/gamecloud/
├── .devcontainer/devcontainer.json   ← Codespace config
├── src/
│   ├── llm/
│   │   ├── base.py                   ← BaseProvider, Message, LLMResponse
│   │   ├── router.py                 ← LLMRouter (multi-provider)
│   │   └── providers/
│   │       ├── openai_provider.py
│   │       ├── anthropic_provider.py
│   │       ├── gemini_provider.py
│   │       └── ollama_provider.py
│   ├── game/
│   │   └── engine.py                 ← GameEngine + GameSession
│   └── main.py                       ← FastAPI app
├── tests/
│   ├── conftest.py
│   ├── test_llm_router.py
│   └── test_game_engine.py
├── .env.template                     ← Key names only, no values
├── requirements.txt
├── Makefile
└── README.md
```
