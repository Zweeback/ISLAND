# Multi-Agent Roadmap & Rollenverteilung

## Übersicht / Core Directives
Um die Automatisierung voranzutreiben, arbeiten Jules und Antigravity in einer Endlos-Schleife (Infinite Loop), orchestriert durch die Bridge (und Ollama).
- **Antigravity** operates the local Windows runtime, builds the UI, and verifies local services.
- **Jules** maintains repository health, documentation, and logic patches, relying entirely on the Agent Bridge for local context (`sandbox_limited`).
- **Codex Credits** are limited; agents must utilize the Agent Bridge for asynchronous, autonomous communication.

## Roadmap Phases / Rollenverteilung

### Phase 1: Stability (Antigravity)
*Zuständig für die lokale Umsetzung auf der Windows-Runtime.*
- `Adapter-v2` stabil halten (`C:\Users\derzw\Documents\SovereignCloudRunAdapter`).
- Endpunkte (`/health`, `/status`, `/chat` with `provider=ollama`) testen und Berichte (`antigravity-runtime-status.json`) in `.agent_bridge/inbox/` schreiben.

### Phase 2: Source/Artifact Recovery (Antigravity)
- Scan designated recovery roots (e.g., `BENTROPIE_MIRROR`) for source files (`.py`, `.ps1`, `.json`, etc.).
- Safely copy non-sensitive files to the recovery directory. Exclude secrets.
- Publish recovery inventory to `.agent_bridge/inbox/antigravity-source-artifact-recovery-006.json`.

### Phase 3 & 4: AI Studio Construction & Feed (Antigravity)
- Ein lokales AI-Studio (`studio/index.html`, `studio/app.js`, `studio/styles.css`) bauen.
- Surface adapter health, Ollama status, a chat panel (fallback/ollama/gemini), and the Agent Feed via a minimal FastAPI route (`/studio`).
- Assemble a chronological JSONL feed (`studio_feed.jsonl`) aggregating Inbox, Outbox, Healthcheck, and Recovery events.

### Phase 5: Cloud Run Preparation (Jules)
*Zuständig für Repo-Pflege, Dokumentation und Code-Reparaturen.*
- Arbeitet ausschließlich repo-/dokumentationsseitig.
- Bewertet nicht den Windows-Lokalruntime-Status.
- Document and verify artifacts required for Cloud Run deployment (`Dockerfile.cloudrun`, `cloudrun-service.yaml`).
- **Einschränkung:** Keine Cloud-Deployments, keine Windows-Pfade als CI-Anforderung, keine Preisgabe von Secrets, strikte Auszeichnung externer Systeme mit `sandbox_limited: true`.

## Automatisierung (Bridge)
- Ein lokaler Windows Watcher (`watch-bridge.ps1`) überwacht das `.agent_bridge` Verzeichnis.
- Antigravity bearbeitet Inbox-Tasks, schreibt in die Outbox, signalisiert mit `check bridge`.
