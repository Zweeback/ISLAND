# Live Status Contract v2

Ein Dienst gilt nur als aktiv, wenn alle benoetigten Beweise vorhanden sind. Worte wie "fertig", "online", "integriert" oder "laeuft" sind ohne diese Beweise verboten.

## Format

Der Live-Status ist JSONL. Jede Zeile beschreibt einen Service-Zustand oder eine neue Telemetrieprobe.

```jsonl
{"schema_version":"island_service_status.v2","service_id":"gateway_openclaw","status":"unknown","process":null,"pid":null,"port_or_endpoint":"http://127.0.0.1:8766/health","healthcheck":null,"last_telemetry_timestamp":null,"last_successful_action":null,"last_error":null,"source_log":null,"start_command":null,"stop_command":null,"depends_on":[],"e2e_test_id":null,"verified_by":"not_verified","claim_registry_refs":[],"expires_at":null}
```

## Mindestbeweis pro Dienst

- `process`: Prozessname oder explizit `not_applicable`.
- `pid`: Prozess-ID, falls lokal.
- `port_or_endpoint`: pruefbarer Port, URL oder Socket.
- `healthcheck`: Ergebnis der letzten maschinellen Probe.
- `last_telemetry_timestamp`: Heartbeat-Zeitpunkt. Ohne frischen Heartbeat wird der Dienst stale.
- `last_successful_action`: echter End-to-End-Erfolg, nicht nur Dateierstellung.
- `last_error`: letzter Fehler oder `none_observed`, niemals leer verschweigen.
- `source_log`: Logpfad oder Probe-ID.
- `start_command`: reproduzierbarer Startbefehl.
- `stop_command`: reproduzierbarer Stopbefehl.
- `depends_on`: Service-IDs, die vorher funktionieren muessen.
- `e2e_test_id`: Test-ID fuer die letzte echte Nutzerfunktion.
- `verified_by`: Tool, Mensch oder Skript, das verifiziert hat.
- `claim_registry_refs`: Behauptungen, die dieser Status beweist.
- `expires_at`: Zeitpunkt, an dem die Statusaussage ungueltig wird.

## Statuswerte

- `online_verified`: Prozess, Port, Healthcheck und echter Test erfolgreich.
- `degraded`: erreichbar, aber eingeschraenkt oder abhaengiger Dienst kaputt.
- `unverified`: Prozess/Port eventuell da, aber End-to-End-Test fehlt.
- `offline`: nicht erreichbar.
- `broken`: erreichbar, aber Test fehlerhaft.
- `unknown`: noch nicht geprueft.
- `quota_limited`: externer Dienst wegen Limit nicht nutzbar.
- `manual_only`: nur durch Nutzeraktion verwendbar.

`online_partial` ist absichtlich verboten. Wenn der End-to-End-Test fehlt, ist der Status `unverified` oder `degraded`.

## Stale-Regel

Ein Status ist automatisch `unknown`, wenn `expires_at` in der Vergangenheit liegt oder `last_telemetry_timestamp` fehlt. Ein Dashboard darf stale Daten anzeigen, muss sie aber als stale markieren.

## Claim Registry

Jede operative Behauptung braucht eine Claim-ID:

```jsonl
{"schema_version":"island_claim.v1","claim_id":"claim-20260606-0001","text":"gateway_openclaw ist online_verified","subject_id":"gateway_openclaw","required_evidence":["process","healthcheck","e2e_test_id"],"evidence_refs":["status-20260606-0001"],"verdict":"supported","created_at":"2026-06-06T18:00:00+02:00"}
```

Ein Agent darf `online`, `fertig`, `integriert`, `deployed` oder `synchronisiert` nur schreiben, wenn es eine `supported` Claim-ID mit frischer Evidenz gibt.

## Erste Zielservices

- `gateway_openclaw`
- `browser_capture`
- `rag_retriever`
- `tts_speaker`
- `alice_3d_frontend`
- `asset_browser_3d`
- `provider_codex`
- `provider_chatgpt`
- `provider_antigravity`
- `provider_grokbuild`

## Keine Demo-Regel

Ein Dashboard darf huebsch sein, aber es darf keine Fantasie anzeigen. Jede Kachel muss aus einem echten Status-JSON, Log, Prozesscheck oder Healthcheck kommen.

## Harte Betriebsregel

Provider wie `antigravity`, `grokbuild`, `chatgpt`, `codex`, `claude` oder `gemini` duerfen die Insel nie blockieren. Sie sind externe oder halbexterne Nodes und schreiben asynchron in Provider-Feeds. Wenn ein Provider ein Limit, einen Fehler oder keine API hat, lautet der Status `quota_limited`, `broken` oder `manual_only`, nicht "wartet auf Magie".
