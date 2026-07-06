# Agent Roadmap: AI Studio & Control Tower

This roadmap outlines the coordinated autonomy loop between the local execution agent (Antigravity) and the repository agent (Jules).

## Core Directives
- **Antigravity** operates the local Windows runtime, builds the UI, and verifies local services.
- **Jules** maintains repository health, documentation, and logic patches, relying entirely on the Agent Bridge for local context (`sandbox_limited`).
- **Codex Credits** are limited; agents must utilize the Agent Bridge for asynchronous, autonomous communication to minimize repetitive querying.

---

## Roadmap Phases

### Phase 1: Stability (Antigravity)
- Monitor and maintain the local `Adapter-v2` instance.
- Ensure `/health`, `/status`, and `/chat` (with `provider=ollama`) endpoints remain operational.
- Output stability state to `.agent_bridge/inbox/antigravity-runtime-status.json`.

### Phase 2: Source/Artifact Recovery (Antigravity)
- Scan designated recovery roots (e.g., `BENTROPIE_MIRROR`) for source files (`.py`, `.ps1`, `.json`, etc.).
- Safely copy non-sensitive files to the recovery directory.
- Exclude secrets (`.env`, keys, tokens).
- Publish recovery inventory to `.agent_bridge/inbox/antigravity-source-artifact-recovery-006.json`.

### Phase 3: AI Studio Construction (Antigravity)
- Build a lightweight local Web UI (`index.html`, `app.js`, `styles.css`) within the `studio/` directory.
- Surface adapter health, Ollama status, a chat panel (fallback/ollama/gemini), and the Agent Feed.
- Integrate a Recovery Panel displaying artifact counts and sensitive file warnings.
- Expose the UI via a minimal FastAPI route (`/studio`).

### Phase 4: Local Feed Assembly (Antigravity & Jules)
- Assemble a chronological JSONL feed (`studio_feed.jsonl`) aggregating Inbox, Outbox, Healthcheck, and Recovery events.
- Surface this feed dynamically within the AI Studio UI.

### Phase 5: Cloud Run Preparation (Jules)
- Document and verify artifacts required for Cloud Run deployment (`Dockerfile.cloudrun`, `cloudrun-service.yaml`).
- Strictly enforce the rule: **No deployment**. Preparation only.

---

*This document is maintained by Jules based on the latest Codex operations plan.*
