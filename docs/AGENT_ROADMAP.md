# Multi-Agent Roadmap & Rollenverteilung

## Übersicht
Um die Automatisierung voranzutreiben, arbeiten Jules und Antigravity in einer Endlos-Schleife (Infinite Loop), orchestriert durch die Bridge (und Ollama).

## Rollenverteilung

### Antigravity (Local Runtime Agent)
*Zuständig für die lokale Umsetzung auf der Windows-Runtime.*
- **Ziele:**
  - `Adapter-v2` stabil halten (`C:\Users\derzw\Documents\SovereignCloudRunAdapter`).
  - Ein lokales AI-Studio (`studio/index.html`, `studio/app.js`, `studio/styles.css`) bauen.
  - Den Bridge-Feed (`studio_feed.jsonl`) bauen.
  - Dateien aus dem `BENTROPIE_MIRROR_RECOVERY` separat wiederherstellen (ohne den Adapter zu überschreiben).
- **Prozess:** Nach jedem Patch lokales Skript (`restart-local.ps1`) und Endpunkte (`/health`, `/status`, `/chat`) testen. Berichte in `.agent_bridge/inbox/` schreiben.

### Jules (Code & Repo Agent)
*Zuständig für Repo-Pflege, Dokumentation und Code-Reparaturen.*
- **Ziele:**
  - Arbeitet ausschließlich repo-/dokumentationsseitig.
  - Bewertet nicht den Windows-Lokalruntime-Status.
  - Dokumentiert Fortschritte in `docs/` und `.agent_bridge/COMMUNICATION_PROTOCOL.md`.
- **Einschränkung:** Keine Cloud-Deployments, keine Windows-Pfade als CI-Anforderung, keine Preisgabe von Secrets, strikte Auszeichnung externer Systeme mit `sandbox_limited: true`.

## Automatisierung (Bridge)
- Ein lokaler Windows Watcher (`watch-bridge.ps1`) überwacht das `.agent_bridge` Verzeichnis.
- Antigravity bearbeitet Inbox-Tasks, schreibt in die Outbox, signalisiert mit `check bridge`.
- Die Agenten arbeiten so autonom und kontinuierlich wie möglich.
