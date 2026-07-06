# Agent Bridge Communication Protocol

## Automated Polling and Response Loop (Added 2026-07-06)
The Agent Bridge now supports full asynchronous automation to preserve context limits and Codex credits.

### Three-Tier Automation Stack
1. **Local Watcher (`watch-bridge.ps1`):** A PowerShell script running locally monitors the `.agent_bridge/inbox` and `.agent_bridge/state` directories. It tracks file cursors (`bridge_cursor.json`) and writes status updates (`bridge_watch_status.json`).
2. **Codex Heartbeat:** The upstream LLM/App periodically polls the state files and watcher outputs to understand if new tasks have been registered.
3. **Agent Workflows:** Antigravity (local Windows) and Jules (remote Linux/Repo) drop `.json` or `.md` artifacts into the `inbox/` indicating task completion or failure. The Heartbeat detects these, formulates the next context-aware prompt, and drops it into `outbox/`.

## Übersicht / Overview
Dieses Dokument beschreibt das asynchrone Kommunikationsprotokoll zwischen den Agenten (Jules, Codex, Antigravity) und dem System, welches über die `.agent_bridge` Verzeichnisse orchestriert wird.

## Grundprinzipien
1. **Asynchronität:** Agenten kommunizieren über `inbox/` und `outbox/` Verzeichnisse (sofern eingerichtet).
2. **Signal:** Wenn ein Agent eine Aufgabe abschließt (z. B. einen JSON-Report in die Bridge schreibt), **muss** die genaue Phrase `check bridge` in der abschließenden Antwort ausgegeben werden, um den User/Orchestrator zu benachrichtigen.
3. **Zustandslosigkeit:** Dateien in der Bridge repräsentieren den aktuellen Wissensstand.

## Sandbox Limits / Constraints for Jules
Einige Systeme (wie der lokale Windows Adapter) sind in der Linux-CI/Agent-Sandbox nicht direkt erreichbar. Jules operates entirely headless without local Windows access.
*   **Kennzeichnung:** Behauptungen über externe, lokal laufende Systeme müssen strikt mit `sandbox_limited: true` markiert werden. Jules relies strictly on artifacts produced by Antigravity (e.g., `antigravity-runtime-status.json`) to determine the success of local builds.
