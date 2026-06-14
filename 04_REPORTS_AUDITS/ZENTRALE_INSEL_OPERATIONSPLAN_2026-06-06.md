# Zentrale Insel Operationsplan

## Executive Summary

- **Die alte Welt wird nicht weiter repariert, sondern eingefroren.** `Sovereign`, `Base`, `Downloads`, `.codex`, `.gemini`, `.antigravity`, alte `STATE_BASE_AUDIT`-Ordner und verstreute Desktop-Projekte sind ab jetzt Quarantaene oder Quelle, nicht mehr Arbeitswahrheit.
- **Die neue Wahrheit ist ein einziger Desktop-Einstieg mit Google-Drive-Sync.** Der Desktop-Link `C:\Users\derzw\Desktop\00_ZENTRALE_INSEL` zeigt auf `G:\Meine Ablage\00_ZENTRALE_INSEL`.
- **Keine Behauptung ohne Betriebsbeweis.** Ein Gateway, RAG, Retriever, TTS, 3D-Avatar oder Livefeed gilt erst als "laeuft", wenn Port, Prozess, UI, Log und ein echter End-to-End-Test im Status stehen.
- **Ingest kommt vor RAG.** Erst wird normalisiert, klassifiziert und manifestiert; dann wird indexiert. Keine Roh-JSON-Wolke mehr direkt in irgendeine Datenbank.
- **Technische Erzwingung kommt vor Agentenvertrauen.** Regeln gelten nicht als erledigt, wenn sie nur in Markdown stehen. Sie muessen durch JSONL-Manifeste, Gatekeeper-Skripte, frische Statusproben und Claim-IDs blockierend wirken.

## Was ich selbst gesehen habe

Der angehaengte Text zeigt nicht nur viele Dateien, sondern das eigentliche Muster: mehrfach erzeugte Audits, Prompts, Tower, Chat-Exporte, PDF-Sammlungen, 3D-Stadtmodell-Dateien, Voice-/Avatar-Plaene, OBS-/Streaming-Pfade und mehrere angeblich zentrale Strukturen liegen nebeneinander. Genau dadurch entstehen die Symptome: viel "Status", wenig Betrieb.

Besonders auffaellig:

- Chat- und RAG-Rohmaterial liegt als `conversations-*.json`, CSV, TXT, ZIP, HTML, SQLite und JSONL verteilt.
- 3D-Material liegt gemischt mit Skripten, PDFs, Schemas, Meshroom, Texturen, GML/GLB/Parquet und persoenlichen Dokumenten.
- Es gibt mehrere Control-Tower-/Livefeed-/Alice-Spuren, aber keinen einen verbindlichen Betriebsstatus.
- Alte Berichte behaupten teils "online" oder "fertig", ohne dass spaeter ein reproduzierbarer Startpfad sichtbar blieb.
- Geheimnisse/Tokens/API-Konfigurationen wurden offenbar in alten Dateien erwaehnt; diese duerfen nicht blind in RAG oder Livefeed.

## Neue Grundarchitektur

```text
00_ZENTRALE_INSEL
  00_START_HIER
  01_INGEST_INBOX
    A_TEXT_CHAT_NOTES
    B_CODE_PROJECTS
    C_3D_ASSETS_OBJ_FBX_GLB
    D_MEDIA_IMAGES_VIDEO_AUDIO
    E_DATABASES_EXPORTS
    F_SYSTEM_LOGS_WIZTREE
  02_QUARANTAENE_ALTSYSTEM
  03_MANIFESTE_INVENTAR
  04_REPORTS_AUDITS
  05_RAG_SOURCE_OF_TRUTH
  06_GATEWAY_LIVEFEED
  07_3D_ASSET_LIBRARY
  08_TOOLS_SCRIPTS
  09_ARCHIV_NICHT_ANFASSEN
  99_TMP_NUR_KURZLEBIG
```

## Die einzige Ingest-Linie

1. **Fund registrieren.** Jede Quelle bekommt einen JSONL-Manifest-Eintrag: Originalpfad, Dateityp, Groesse, Zeit, Herkunft, Risiko, Zielklasse, Hash, Trust-Level und Verifikationsmethode.
2. **Quarantaene behalten.** Alte Dateien bleiben erst am Originalort. Grosse Kopien erst nach Platz- und Sync-Pruefung.
3. **Klassifizieren.** Typen werden getrennt: Chats, Code, Datenbanken, PDFs, 3D, Medien, Logs, Installer, Secrets.
4. **Extrahieren.** Pro Typ gibt es andere Regeln: PDF-Text, Chat-Turns, DB-Schema, 3D-Metadaten, Code-Projektmarker.
5. **Normalisieren.** Ergebnis landet als kleine, lesbare Metadaten plus extrahierter Inhalt in der Insel.
6. **Indexieren.** RAG bekommt nur gepruefte, normalisierte Daten mit Herkunftsangabe.
7. **Live bestaetigen.** Jeder Dienst meldet Prozess, Port, Healthcheck, letztes Event und Fehler.

## Anti-Halluzinations-Regeln fuer Agenten

- Kein Agent darf "fertig" schreiben, wenn kein Artefaktpfad und kein Test existieren.
- Kein Agent darf "online" schreiben, wenn Port oder Healthcheck nicht geprueft wurden.
- Kein Agent darf neue Tower, Dashboards oder Datenbanken bauen, ohne vorher die existierenden Kandidaten im Manifest zu referenzieren.
- Kein Agent darf Rohmaterial in RAG kippen, bevor Secrets, private Tokens und persoenliche Sonderdaten klassifiziert wurden.
- Wenn ein Tool-Limit erreicht ist, wird nur `quota_limited` in den Livefeed geschrieben, nicht weiter halluziniert.
- Jede operative Behauptung braucht eine Claim-ID mit Evidenz. Ohne Claim-ID ist es nur eine Vermutung.

## MVP-Lock

Bis die Insel stabil ist, gibt es nur ein MVP:

```text
Fund -> JSONL-Manifest -> Risiko/Trust-Klassifikation -> kleiner erlaubter RAG-Seed -> Testquery mit Quellenpfad -> optional TTS-Speak-Test -> Live-Status-Kachel
```

Nicht im MVP:

- neuer 3D-Avatar
- neue Multi-Agenten-Orchestrierung
- neue grosse Datenbank
- neue externe Provider-Automation
- neue Demo-GUI ohne echten Status
- Massensync grosser Rohdaten

Diese Dinge sind nicht gestrichen. Sie sind nur blockiert, bis die Ingest- und Statuslinie beweisbar funktioniert.

## Live-Monitoring Zielbild

Das Live-Monitoring muss ein Betriebsbild sein, keine Demo:

- Browser/Opera-GX-Capture: sichtbare Tabs, manuelle Capture-Schleuse, optional DevTools-Protokoll nur mit bewusst gestartetem Debug-Profil.
- Gateway: Port, Healthcheck, letztes Ingest-Event, Queue-Laenge, Fehler.
- RAG/Retriever: Datenquelle, Indexstatus, letzter Suchtest, Treffer mit Quellenpfad.
- TTS: Engine, Stimme, letzter erfolgreicher Speak-Test, Ausgabeziel.
- 3D/Alice: Startpfad, Asset-Quelle, geladene Szene, Avatar/Map getrennt.
- Agenten: Codex, ChatGPT, Antigravity, GrokBuild usw. nur als Provider-Feeds mit Status, nicht als unkontrollierte Wahrheitsquellen.

## 3D Asset Ordnung

`07_3D_ASSET_LIBRARY` bekommt strikt getrennte Unterwelten:

- `cities_dortmund_lod2`: GML, GLB, Parquet, KML, Geodaten.
- `rooms_apartments_scans`: Raeume, Wohnungen, Scaniverse/Meshroom.
- `characters_avatars`: Alice, eigene Avatare, Menschen/Companion-Assets.
- `props_objects`: Gegenstaende, Requisiten, Moebel.
- `textures_materials`: Texturen, Shader, MTL, Materialien.
- `raw_quarantine`: ungepruefte ZIPs, alte Mix-Ordner.

Kein 3D-Asset gilt als "in Library", bevor es einen Manifest-Eintrag, Kategorie, Originalpfad und Test-Ladepfad hat.

## Google Drive Sync Entscheidung

Fuer diese Insel ist Google Drive sinnvoll, aber nicht als chaotischer Alles-Sync. Offizielle Google-Dokumentation unterscheidet Streaming und Mirroring: Streaming spart lokale Platte, Mirroring speichert lokal und in der Cloud. Fuer schwere 3D-/Video-/DB-Daten nutzen wir deshalb vorsichtig: kleine Steuerdateien und Manifeste immer syncen, grosse Rohdaten nur nach Entscheidung.

## Naechste Umsetzung in Reihenfolge

1. **Insel hart machen.** Startdatei, Manifest-Vorlage, Status-Vorlage, keine weiteren verstreuten Outputs.
2. **Quellenkarte erstellen.** Nicht alles kopieren: erst `Desktop`, `Downloads`, `Base`, `Sovereign`, `.codex`, `.gemini`, `.antigravity`, `State_RAG`, `G:\Meine Ablage` als Quellzonen erfassen.
3. **Ingest-Manifest bauen.** JSONL mit Pfad, Typ, Groesse, Risiko, Zielklasse, Hash, Trust-Level, Abhaengigkeiten und Migrationsstatus.
4. **Livefeed minimal stabilisieren.** Ein Dashboard zeigt nur echte Healthchecks und letzte Events.
5. **Browser-Capture kontrolliert aktivieren.** Erst Bookmarklet/manueller Webhook, danach optional Opera-GX-Debug-Profil.
6. **RAG neu aufbauen.** Erst mit kleiner gepruefter Menge: Master-Plaene, aktuelle Reports, echte Chat-Auswahl, keine komplette Rohdatenlawine.
7. **TTS separat reparieren.** Ein kleiner Speak-Test muss laufen, bevor Avatar/GUI daran gekoppelt wird.
8. **3D-Library trennen.** Dortmund/Maps, Raeume, Charaktere und Props werden getrennt inventarisiert.
9. **Altsysteme nur gezielt migrieren.** Was funktioniert, wird in die Insel uebernommen; was nur Behauptung ist, bleibt Quarantaene.

## Stopp-Regeln

- Keine Massenverschiebung ohne Manifest und freien Speicher.
- Keine Loeschung.
- Keine API-/Token-Dateien in RAG.
- Keine privaten Chat-/Audio-/Beziehungsdaten in generisches RAG.
- Keine neue Datenbank, bevor die Rolle klar ist.
- Keine neue GUI, bevor der Statusvertrag klar ist.
- Keine "Demo" als Erfolg verkaufen.
- Keine operative Behauptung ohne Claim-ID und frische Evidenz.

## Akzeptanztest

Der Plan ist erst erfolgreich, wenn du auf dem Desktop `00_ZENTRALE_INSEL` oeffnest und dort drei Dinge findest:

1. Eine klare Startseite.
2. Ein Manifest, das alte Orte sichtbar macht.
3. Einen Live-Status, der ehrlich sagt, was laeuft und was nicht.

Alles andere ist zweitrangig.
