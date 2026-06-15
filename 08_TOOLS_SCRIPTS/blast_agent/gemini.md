# B.L.A.S.T. Agent Project Map (gemini.md)

This file is the "Source of Truth" for the B.L.A.S.T. Local Agentic System project state, data schemas, and behavioral rules.

---

## 1. Project Context & Objectives

* **North Star**: Build a deterministic local agent system (`blast_agent.py`) that can scrape key data sources (Digibib, Scribd, Statista, LinkedIn, OpenData Dortmund), catalog local PC file structures (Desktop, Sovereign, etc.), and self-heal on execution failures.
* **Integrations**: Digibib (lobid API + login session), Scribd, Statista, LinkedIn (`li_at` cookie), OpenData Dortmund (Explore API v2.1).
* **Delivery**: Output structured JSON/Markdown reports into `.tmp/` and automatically catalog files into `system_map.json`.

---

## 2. Active Development Phase

* **Current Phase**: **Phase 1 - Blueprint & Scaffolding**
* **Status**: Initializing directory structures, `.env` templates, `.context/` configuration, and Markdown SOPs.

---

## 3. Data Schema Definitions

### Input Credentials Shape (`.env`)

```bash
OPENAI_API_KEY=sk-proj-xxx
GITHUB_TOKEN=ghp_xxx

# Digibib Dortmund
DIGIBIB_BARCODE=xxx
DIGIBIB_PASSWORD=xxx

# Scribd
SCRIBD_USER=xxx
SCRIBD_PASS=xxx
SCRIBD_COOKIE=xxx

# Statista
STATISTA_USER=xxx
STATISTA_PASS=xxx
STATISTA_COOKIE=xxx

# LinkedIn
LINKEDIN_COOKIE_LI_AT=xxx

# Dortmund Open Data
DORTMUND_OPEN_DATA_KEY=xxx
```

### Scraping Output Shape (JSON)

```json
{
  "source": "opendata_dortmund / digibib / scribd / statista / linkedin",
  "query": "string",
  "timestamp": "ISO-8601 String",
  "results_count": 0,
  "records": [
    {
      "title": "string",
      "url": "string",
      "snippet": "string",
      "metadata": {}
    }
  ]
}
```

---

## 4. Maintenance & Execution Log

* **2026-06-14**: Project initialized. Created master `Workspace.md` and B.L.A.S.T. agent scaffolding folder structure. SOPs drafted.
* **Next Action**: Create `blast_agent.py` and write the scraper modules under `tools/`.

* **2026-06-15T13:50:15.507430+00:00**: Executed scraper_opendata_dortmund with ['search_datasets', 'Bibliotheken']. Reason: OpenData Dortmund API is public and does not require credentials. Let's do a public dry-run search.
