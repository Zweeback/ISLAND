# Zentrale Insel Workspace Map & Integration Roadmap

Welcome to the **Zentrale Insel Master Workspace**. This document serves as the central directory, architecture map, and execution roadmap for connecting your local PC environment, online resources (Digibib, Scribd, Statista, LinkedIn, OpenData Dortmund), and AI tools (KIs, Firebase, Genkit).

---

## 1. Current Status (Status-Quo)

* **Workspace Root**: `c:\Users\derzw\Desktop\00_ZENTRALE_INSEL`
* **Core Folders**:
  * `00_START_HIER/`
  * `01_INGEST_INBOX/` (Target for incoming documents and automatic processing)
  * `02_QUARANTAENE_ALTSYSTEM/`
  * `03_MANIFESTE_INVENTAR/`
  * `05_RAG_SOURCE_OF_TRUTH/`
  * `08_TOOLS_SCRIPTS/` (Contains orchestration and scraper scripts)
  * `99_TMP_NUR_KURZLEBIG/` (Temporary working area)
* **API Keys & Credentials**:
  * **Loaded**: `OPENAI_API_KEY`, `GITHUB_TOKEN` (used for agent thinking and code syncing).
  * **Pending Local Configuration**: Digibib (Ausweis + PIN), Scribd, Statista, LinkedIn (`li_at` session cookie).
* **Reference Texts**: 16 files successfully extracted to `C:\Users\derzw\.gemini\antigravity-ide\scratch\extracted_text\`.
  * *Note on Scanned PDFs*: Three files (`1014027619-Google-Antigravity-Agentic-Platform-compressed.pdf`, `1046103511-google-antigravity.pdf`, and `982349709-Google-Antigravity-Three-Things-at-Once.pdf`) are scanned images and contain no embedded text.

---

## 2. API & Data Source Catalog

### Local Sources

* **Local Dateisystem (PC-Scan)**: Desktop, Sovereign folder, and subfolders. Requires strict exclusion lists (`.git`, `node_modules`, `.ssh`, sensitive credentials) to prevent performance hits and security risks.
* **Google Drive**: Mounted under `G:\Meine Ablage`.
* **Knowledge Items (KIs)**: Located in `AppData\Local\Knowledge`.

### Online Sources

| Platform | Access Type | API / Scraping Method | Authentication Needed | Status |
| :--- | :--- | :--- | :--- | :--- |
| **OpenData Dortmund** | Public API | Opendatasoft Explore API v2.1 | None (Public) | Ready |
| **Digibib (Dortmund)** | Scraper / API | lobid.org (hbz Metadaten) + Form POST fallback | Card Barcode & PIN | Planned |
| **Scribd** | Scraper | requests.Session / Playwright | Session Cookie or Login | Planned |
| **Statista** | Scraper | Playwright (HTML table extraction) | Session Cookie or Login | Planned |
| **LinkedIn** | Scraper | `li_at` session cookie authentication | Session Cookie | Planned |
| **Firebase / Genkit** | MCP Integration | Native Firebase MCP toolset | Local login | Active |

---


### Gemini / Antigravity Managed Apps
The system catalogs and manages a suite of applications generated via Gemini/Antigravity, ensuring they are integrated into the master workspace. These include:
- **Game Dev & Simulation**: GTA Dortmund (2D canvas sandbox), RealityForge 3D, Massive Multiplayer Laser Tag, Synthwave Space
- **Tools & Productivity**: Promtedex, ScriptBoard AI, DevSkills Cockpit, Forensik-Dashboard, Gemini OS
- **Creative & Audio**: Music Mashup Studio, Lyria Studio, AI Talk Radio, EchoPaths, PromptDJ
- **3D & Spatial**: FeedNoodle Spatial Browser, 3D Knowledge Graph, Aura AI Companion, Gothic Witch and Caregiver 3D Companion, Bitscape Sandbox

All applications are indexed in the `03_MANIFESTE_INVENTAR/island_manifest.jsonl` under the `code_project` artifact family.

## 3. Digibib Integration Critical Analysis

* **How it works**: Digibib Dortmund (`stlb-dortmund.digibib.net`) runs on the hbz IntrOX Metasearch platform. There is no official public REST API for direct catalog search or user account manipulation.
* **Implementation Strategy**:
  1. **Public Catalog Metadata**: Query the public [lobid.org](https://lobid.org/) API (hbz Linked Open Data) for stable, structured metadata searches.
  2. **Authenticated Actions**: Use a `requests.Session` form post login to `stlb-dortmund.digibib.net` to query personal loans, extend deadlines, and download licensed PDFs.
  3. **Fallback**: Playwright headless browser login if JS/CSRF tokens change.
* **Ethics/Rate Limiting**: Query intervals must be capped at 1-2 calls per minute.

---

## 4. Local PC Inventory Strategy

To catalogue your entire PC without slowing down your machine, we implement a **Phased, Incremental Indexer**:

1. **Scope Limit**: Default index scanning is limited to specific paths: `Desktop`, `Downloads`, `00_ZENTRALE_INSEL`, and `G:\Meine Ablage`.
2. **Exclusion Rules**: Exclude system directories (`AppData`, `Program Files`, Windows files) and massive code dependency folders (`node_modules`, `venv`, `.git`).
3. **Storage**: Save file paths, sizes, and modification timestamps into a local SQLite database or unified `system_map.json`.
4. **Knowledge Coupling**: Link indexed files to relevant KIs and project components.

---

## 5. Implementation Roadmap (B.L.A.S.T.)

### Phase 1: Core Scaffolding & Rules (Current)

* [ ] Create `08_TOOLS_SCRIPTS/blast_agent/` directory structure.
* [ ] Initialize `gemini.md` Project Map.
* [ ] Write standard operating procedures (SOPs) in `architecture/`:
  * `sop_agent_run.md` (Agent reasoning & self-healing).
  * `sop_scrapers.md` (Rate limits, cookie management).
* [ ] Create `.env.template` showing expected secrets.

### Phase 2: Scrapers & Connections

* [ ] Implement `scraper_opendata_dortmund.py` (Verify via public API test).
* [ ] Implement `scraper_digibib.py` (Verify via lobid.org search and local credentials).
* [ ] Implement `scraper_scribd.py` and `scraper_statista.py`.
* [ ] Implement `scraper_linkedin.py` (Uses `li_at` cookie).

### Phase 3: PC Indexing & Ingestion

* [ ] Implement `inventory_compiler.py` for recursive file indexing.
* [ ] Build `01_INGEST_INBOX` automation watcher (auto-RAG and summary updates).

### Phase 4: Trigger & Self-Healing

* [ ] Connect Firebase MCP toolset to automatically deploy scraped summaries/pages.
* [ ] Enable self-healing loop: Agent uses Google search to fix scraper HTML changes.
