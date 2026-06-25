# Codex Agent Instructions

Welcome, Codex. This document outlines coding standards and guidelines for working within the **Zentrale Insel Master Workspace**.

## 1. Coding Standards
- Write clean, maintainable, and well-documented Python code.
- Follow PEP 8 guidelines.
- Handle exceptions gracefully and provide informative error messages or logs.

## 2. Python Scripting Best Practices
- **Path Resolution:** Avoid hardcoded Windows paths (e.g., `C:\Users\...`). Always use dynamic path resolution to ensure cross-environment compatibility.
  - Example: `from pathlib import Path; WORKSPACE_ROOT = Path(__file__).resolve().parent.parent`
- Use the `pathlib` module for all path operations instead of `os.path`.

## 3. Workspace Structure
Familiarize yourself with the numbered directory structure. Empty directories should be tracked in Git using `.gitkeep` files.
- `00_START_HIER/`
- `01_INGEST_INBOX/` (Target for incoming documents and automatic processing)
- `02_QUARANTAENE_ALTSYSTEM/`
- `03_MANIFESTE_INVENTAR/`
- `04_REPORTS_AUDITS/`
- `05_RAG_SOURCE_OF_TRUTH/`
- `06_GATEWAY_LIVEFEED/`
- `08_TOOLS_SCRIPTS/` (Contains orchestration and scraper scripts, notably the `blast_agent` application)
- `09_ARCHIV_NICHT_ANFASSEN/`
- `99_TMP_NUR_KURZLEBIG/` (Temporary working area)

## 4. Credentials and Secrets Handling
- Agent configurations, API keys, credentials, and session cookies must be loaded from `08_TOOLS_SCRIPTS/blast_agent/.env`.
- Ensure `.env` is strictly excluded from version control (check `.gitignore`). Use `.env.template` for tracking required secret names.
- Never hardcode secrets in any script or markdown file.
