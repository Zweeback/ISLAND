# Ingest Manifest Schema v2

Jede Datei, jeder Ordner, jeder Dienst, jede Datenbank, jedes Projekt und jede relevante Behauptung bekommt genau einen Eintrag. Ohne validen Manifest-Eintrag kein RAG, kein Livefeed, keine Migration.

## Format

Das Manifest ist strikt JSONL, nicht CSV. Eine Zeile ist ein valides JSON-Objekt. CSV ist fuer Pfade, Kommas, Notizen und Agenten-Ausgaben zu fragil.

```jsonl
{"schema_version":"island_manifest.v2","id":"src-20260606-0001","artifact_family":"chat_archive","object_kind":"file","discovered_at":"2026-06-06T17:00:00+02:00","source_path":"/workspace/STATE_BASE_AUDIT/conversations-001.json","source_zone":"Desktop","origin_type":"user_export","size_bytes":0,"content_hash_sha256":null,"duplicate_group":null,"risk_class":"private","trust_level":"unverified","knowledge_domain":["chat","personal"],"target_lane":"05_RAG_SOURCE_OF_TRUTH","lifecycle_state":"DISCOVERED","owner":"manual","depends_on":[],"used_by":[],"rag_allowed":false,"livefeed_allowed":false,"last_verified":null,"verification_method":"not_verified","verification_evidence":null,"verification_expiry":null,"next_action":"secret_scan_then_extract_chat_turns","notes":"ChatGPT export candidate"}
```

## Feldbedeutung

- `schema_version`: aktuell `island_manifest.v2`.
- `id`: stabile Kurz-ID, z.B. `src-20260606-0001`.
- `artifact_family`: fachliche Familie, z.B. `chat_archive`, `rag_database`, `livefeed_dashboard`, `city_model`, `voice_system`, `audit_report`, `service_status`, `code_project`.
- `object_kind`: `file`, `folder`, `service`, `database`, `project`, `concept`, `claim`.
- `discovered_at`: Datum/Uhrzeit der Sichtung.
- `source_path`: Originalpfad, unveraendert.
- `source_zone`: z.B. `Desktop`, `Downloads`, `Base`, `Sovereign`, `Codex`, `Gemini`, `Antigravity`, `GoogleDrive`.
- `origin_type`: `user_created`, `user_export`, `ai_generated`, `downloaded`, `library_source`, `system_generated`, `unknown`.
- `size_bytes`: Groesse, wenn bekannt.
- `content_hash_sha256`: Hash fuer Objektidentitaet und Deduplizierung, sobald berechnet.
- `duplicate_group`: gemeinsame Gruppe fuer erkannte Duplikate, z.B. `dup-00015`.
- `risk_class`: `safe`, `private`, `secret_risk`, `binary_unknown`, `corrupt_or_duplicate`, `needs_review`.
- `trust_level`: `verified`, `semi_verified`, `unverified`, `hallucinated`, `compromised`.
- `knowledge_domain`: Liste, z.B. `["dortmund","3d","geodata"]` oder `["personal","chat"]`.
- `target_lane`: Ziel in der Insel, z.B. `05_RAG_SOURCE_OF_TRUTH` oder `07_3D_ASSET_LIBRARY`.
- `lifecycle_state`: `DISCOVERED`, `CLASSIFIED`, `QUARANTINED`, `VERIFIED`, `MIGRATED`, `INDEXED`, `ACTIVE`, `REJECTED`.
- `owner`: `manual`, `codex`, `alice`, `antigravity`, `unknown`.
- `depends_on`: Liste von Manifest-IDs, ohne die dieses Objekt nicht nutzbar ist.
- `used_by`: Liste von Manifest-IDs, die dieses Objekt verwenden.
- `rag_allowed`: Boolean. Darf nur nach Klassifikation und Schutzregeln `true` sein.
- `livefeed_allowed`: Boolean. Darf nur fuer nicht-sensitive Betriebsdaten `true` sein.
- `last_verified`: letzter echter Pruefzeitpunkt.
- `verification_method`: z.B. `file_exists`, `sha256_hash`, `service_port_open`, `healthcheck_http_200`, `manual_review`, `not_verified`.
- `verification_evidence`: Pfad, Healthcheck-ID, Log-ID oder Claim-ID.
- `verification_expiry`: Zeitpunkt, nach dem die Verifikation wieder als stale gilt.
- `next_action`: naechster konkreter Schritt.
- `notes`: kurze Erklaerung, keine Romane.

## Lebenszyklus

```text
DISCOVERED -> CLASSIFIED -> QUARANTINED -> VERIFIED -> MIGRATED -> INDEXED -> ACTIVE
```

`REJECTED` ist ein erlaubter Endzustand. `ACTIVE` ist nur erlaubt, wenn `last_verified`, `verification_method`, `verification_evidence` und nicht abgelaufene `verification_expiry` vorhanden sind.

## Harte Regeln

- `secret_risk`, `private`, `binary_unknown` und `compromised` duerfen nie direkt in generisches RAG oder Livefeed.
- `rag_allowed=true` ist nur erlaubt, wenn `risk_class=safe`, `trust_level` mindestens `semi_verified`, ein Hash oder eine andere robuste Verifikation vorhanden ist und `verification_expiry` nicht abgelaufen ist.
- `livefeed_allowed=true` ist nur erlaubt fuer Betriebsstatus, nicht fuer private Chatinhalte, Tokens, persoenliche Audio-Dateien oder ungepruefte AI-Berichte.
- AI-generierte Berichte starten immer mit `trust_level=unverified`, bis ein lokaler Faktencheck sie bestaetigt.
- Ein Objekt ohne `content_hash_sha256` darf nicht dedupliziert oder migriert werden, ausser es ist ein Dienst/Concept/Claim ohne Dateikoerper.
- Ein Objekt darf nicht in RAG indexiert werden, wenn seine Abhaengigkeiten in `depends_on` nicht `VERIFIED` oder `ACTIVE` sind.

## Minimaler MVP-Fokus

Fuer den Start werden nur diese Familien aktiv verfolgt:

- `source_zone_inventory`
- `chat_archive`
- `rag_seed_document`
- `service_status`
- `livefeed_dashboard`
- `3d_asset`

Alles andere bleibt `DISCOVERED` oder `QUARANTINED`, bis die Minimal-Ingest-Linie stabil laeuft.
