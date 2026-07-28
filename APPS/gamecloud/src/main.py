"""
GameCloud FastAPI server.

Endpoints
─────────
GET  /status              – provider health & model list
POST /chat                – raw multi-LLM chat
POST /game/session        – start a new game session
POST /game/{session_id}   – take a game step
GET  /game/{session_id}   – read session state
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.llm.providers import Message
from src.llm.router import LLMRouter
from src.game.engine import GameEngine, GameSession

# ── App init ─────────────────────────────────────────────────────────────────

_router: LLMRouter
_engine: GameEngine
_sessions: dict[str, GameSession] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _router, _engine
    _router = LLMRouter()
    _engine = GameEngine(router=_router)
    yield


app = FastAPI(
    title="GameCloud Multi-LLM API",
    version="0.1.0",
    description="Cloud game API backed by OpenAI, Anthropic, Gemini, and Ollama.",
    lifespan=lifespan,
)


# ── Schema ───────────────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    messages: list[dict[str, str]]
    provider: str | None = None
    model: str | None = None
    max_tokens: int = 2048
    temperature: float = 0.7


class ChatResponse(BaseModel):
    content: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int


class NewSessionRequest(BaseModel):
    initial_state: dict[str, Any] = {}
    provider: str | None = None
    model: str | None = None


class StepRequest(BaseModel):
    player_input: str


# ── Routes ───────────────────────────────────────────────────────────────────


@app.get("/status")
def get_status() -> dict:
    return {
        "env": os.getenv("GAMECLOUD_ENV", "development"),
        "providers": _router.status(),
        "available": _router.available_providers(),
    }


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    messages = [Message(role=m["role"], content=m["content"]) for m in req.messages]
    try:
        resp = _router.chat(
            messages=messages,
            provider=req.provider,
            model=req.model,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ChatResponse(
        content=resp.content,
        model=resp.model,
        provider=resp.provider,
        input_tokens=resp.input_tokens,
        output_tokens=resp.output_tokens,
    )


@app.post("/game/session")
def new_session(req: NewSessionRequest) -> dict:
    session = _engine.new_session(req.initial_state)
    _sessions[session.session_id] = session
    return {"session_id": session.session_id, "state": session.state}


@app.get("/game/{session_id}")
def get_session(session_id: str) -> dict:
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session.session_id,
        "state": session.state,
        "history": session.history,
    }


@app.post("/game/{session_id}")
def game_step(session_id: str, req: StepRequest) -> dict:
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        narration = _engine.step(session, req.player_input)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "session_id": session_id,
        "narration": narration,
        "state": session.state,
    }
