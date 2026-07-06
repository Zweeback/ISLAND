# Agent Bridge Communication Protocol

## Übersicht
Dieses Dokument beschreibt das asynchrone Kommunikationsprotokoll zwischen den Agenten (Jules, Codex, Antigravity) und dem System, welches über die `.agent_bridge` Verzeichnisse orchestriert wird.

## Grundprinzipien
1. **Asynchronität:** Agenten kommunizieren über `inbox/` und `outbox/` Verzeichnisse (sofern eingerichtet).
2. **Signal:** Wenn ein Agent eine Aufgabe abschließt (z. B. einen JSON-Report in die Bridge schreibt), **muss** die genaue Phrase `check bridge` in der abschließenden Antwort ausgegeben werden, um den User/Orchestrator zu benachrichtigen.
3. **Zustandslosigkeit:** Dateien in der Bridge repräsentieren den aktuellen Wissensstand.

## Sandbox Limits
Einige Systeme (wie der lokale Windows Adapter) sind in der Linux-CI/Agent-Sandbox nicht direkt erreichbar.
*   **Kennzeichnung:** Behauptungen über externe, lokal laufende Systeme müssen strikt mit `sandbox_limited: true` markiert werden.
