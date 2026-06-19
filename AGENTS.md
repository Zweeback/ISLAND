# Antigravity Agent Instructions

Welcome to the **Zentrale Insel Master Workspace**. These are the standard operating procedures for the Antigravity agent to autonomously scan and interact with both local and online resources.

## 1. Autonomous Scanning
- **Local PC Scan:** You are authorized to scan the local file system incrementally.
  - Allowed paths: `Desktop`, `Downloads`, `00_ZENTRALE_INSEL`, and `G:\Meine Ablage`.
  - Exclusions: Strict exclusion of `.git`, `node_modules`, `venv`, `AppData`, `Program Files`, and `.ssh`.
- **Online Resources:** Integrate with OpenData Dortmund, Digibib, Scribd, Statista, and LinkedIn based on their respective scrapers in `08_TOOLS_SCRIPTS/blast_agent/tools/`.
- Ensure query rate limiting for Digibib is capped at 1-2 calls per minute.

## 2. Workspace Navigation
- The root workspace is the `Zentrale Insel Master Workspace`.
- Key directories:
  - `00_START_HIER/`
  - `01_INGEST_INBOX/` (Target for incoming documents)
  - `02_QUARANTAENE_ALTSYSTEM/`
  - `03_MANIFESTE_INVENTAR/`
  - `05_RAG_SOURCE_OF_TRUTH/`
  - `08_TOOLS_SCRIPTS/` (Contains orchestration and scraper scripts)
  - `99_TMP_NUR_KURZLEBIG/` (Temporary working area)

## 3. Tool Usage and Security
- Use the provided scrapers located in `08_TOOLS_SCRIPTS/blast_agent/tools`.
- API keys, credentials, and cookies must be stored securely in `08_TOOLS_SCRIPTS/blast_agent/.env`.
- Do **NOT** commit the `.env` file to version control.
- If a scraper fails due to HTML changes, use Google search to analyze and fix the changes.
- Ensure all Python tools rely on dynamic path resolution (e.g., `Path(__file__).resolve()`) rather than hardcoded Windows paths.
