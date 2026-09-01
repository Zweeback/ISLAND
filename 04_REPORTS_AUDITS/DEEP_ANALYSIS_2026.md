# 🔍 Tiefenanalyse: ISLAND Monorepo & Zentrale Insel (Status 2026)

**Datum:** 2026-07-21
**Kontext:** Zentrale Insel Master Workspace, Gamedev Autonomy, Anti-Gravity Bridge

Diese Dokumentation fasst alle offenen Fragen (explizit/implizit), Projektideen, Interaktionsmuster, Flags, verborgene Informationen und das Secret-Management zusammen.

---

## 1. Offene Fragen (Explizit & Implizit)

### Explizite Fragen
* **OpenClaw Gateway:** Wird derzeit als optional/Kandidat behandelt. Wie wird die genaue Wiederanbindung an die lokale MSI-Maschine (G75 9SC) realisiert, nachdem das vorherige Asus-Gateway ersetzt wurde?
* **Google Drive Sync:** Eine Entscheidung für "Streaming vs. Mirroring" wurde getroffen (Vermeidung von Massensync). Aber wie wird der inkrementelle Abgleich von kleinen Steuerdateien vs. großen 3D-Rohdaten in der Praxis automatisiert, ohne das MVP-Lock zu verletzen?
* **VRAM Arbitration:** Wie genau steuert die Anti-Gravity Bridge das Entladen von Ollama (`keep_alive: 0`) im Konfliktfall mit CUDA-Rendering (Blender/Meshroom) sicher über Prozess-Semaphoren?

### Implizite Fragen
* **Agenten-Kollision:** Wenn Jules, Codex und Antigravity gleichzeitig auf `repos_merged.jsonl` oder die `.agent_bridge`-Inbox zugreifen, wie werden Race Conditions vermieden?
* **3D-Asset-Pipeline (ALICE):** Wie wird der Übergang von rohen Scans (`raw_quarantine`) in saubere, geriggte GLB-Modelle (`characters_avatars`) automatisiert, wenn JIT-Guarding greift?

---

## 2. Projektideen & Potenziale

* **GTA Dortmund (Gamedev Autonomy):** Das erste voll autonome Build-Target. Das Potenzial liegt in der Kombination von OpenData Dortmund (Geodaten, Bibliotheken), 3D-Assets (LOD2-Modelle) und Agenten, die Mechaniken und Entitäten automatisch via GRIMM als Knowledge Graph aufbauen.
* **B.L.A.S.T. / Antigravity Bridge:** Eine mächtige Brücke zwischen der Linux-Container-Welt (Jules) und der lokalen Windows-Ausführungsebene. Erlaubt hochkomplexe Workflows (z. B. Blender-Automatisierung, Photogrammetrie) unter JIT-Ressourcenüberwachung.
* **Semantische Datenauswertung (GRIMM & Feednoodle):** Strukturierte Visualisierung von RAG-Daten, Chat-Exports und Scraping-Ergebnissen (Digibib, LinkedIn, Statista) im 3D-Raum (Spatial Browser).

---

## 3. Interaktionsmuster & Agenten-Architektur

* **Asynchrone Brücken-Kommunikation:** Kommunikation zwischen lokaler Maschine und Cloud/Jules erfolgt streng über das `.agent_bridge`-Verzeichnis (`inbox/`, `outbox/`, `state/`) mit PowerShell-Watchern (`watch-bridge.ps1`). Nach Task-Ende wird `check bridge` ausgegeben.
* **Single Source of Truth:** `03_MANIFESTE_INVENTAR` (JSONL-Dateien) ist die einzige Quelle. Keine "blinden" Syncs oder Annahmen ohne Manifest-Eintrag.
* **Rollenverteilung:**
  * **Jules:** Cloud-Koordinator, PRs, Code-Patches (Headless).
  * **Codex:** Lokaler Scanner, Registry-Builder, CSV-Klassifikation.
  * **Antigravity:** Windows-Workbench, AI Studio Mapping, Heavy-Lifting (3D, Unity).
* **MVP-Lock ("Ingest kommt vor RAG"):** Fund -> Manifest -> Klassifikation -> RAG-Seed -> Test -> Live-Status.

---

## 4. Flags, Hidden Infos & Anti-Halluzinations-Regeln

* **`sandbox_limited: true`:** Ein wichtiges Flag, das Jules setzen muss, wenn lokale Zustände nicht verifiziert werden können. Verhindert das Halluzinieren von Erfolgen.
* **JIT Guarding:** Bevor Heavy-Tasks (Meshroom/Blender) starten, wird Telemetrie geprüft. Reicht der RAM/VRAM nicht, wird der Task zurückgestellt (Deferred Queue).
* **Logische vs. Empirische Provenienz:** Unterscheidung zwischen dem "Was sollte passieren?" (Input-Hashes, AST) und dem "Was ist wirklich passiert?" (Telemetrie, Hardware-Limits). SHA-256-Identität ist in stochastischen GPU-Pipelines nicht garantiert.
* **`trust_level` & `risk_class`:** Jede Datei im JSONL-Manifest erhält Trust- und Risk-Scores (z. B. `hallucinated`, `unverified`, `private`). Rohmaterial geht niemals ungefiltert ins generische RAG.

---

## 5. Secret Management & Sicherheit

* **Strikte Hygiene:** Credentials (API Keys für OpenAI, GitHub, Digibib, Cookies) sind radikal aus dem Code verbannt. Placeholder wie `sk-proj-xxx` oder `ghp_xxx` werden verwendet, um Secret-Scanner (False-Positives) nicht auszulösen.
* **Umgebungsvariablen:** Geladen über `.env`-Dateien (z. B. in `08_TOOLS_SCRIPTS/blast_agent/`), welche über strikte `.gitignore`-Regeln vom Versionskontrollsystem ausgeschlossen sind.
* **Sicherheit im Code:** Vermeidung von `shell=True` (Command Injection Risiko) und Vermeidung fest codierter lokaler Windows-Pfade (z. B. `C:\Users\...`), stattdessen dynamische Pfadauflösung (`Path.home()`, `Path(__file__).resolve()`).
