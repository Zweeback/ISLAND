# ISLAND Agent Governance

This file defines workspace-wide operating procedures for all agents working in
this repository (Antigravity, Jules, Codex, Gemini, GitHub Copilot Cloud Agent,
and any external web-based AI tools).

Project-specific rules override these defaults. Closer `AGENTS.md` files in
subdirectories take precedence over this root file.

---

## 1. Workspace Identity and Catalog

ISLAND is a **consolidation monorepo**, not a production platform.
The authoritative list of all projects (active, placeholder, archived, data-only)
is in:

```
workspace/projects.yaml
```

Always consult this catalog before assuming where a project lives or what its
status is. Do **not** invent project paths, deployment targets, or dependencies
that are not in the catalog.

---

## 2. P0 Security Blockers

The following open PRs contain unresolved security vulnerabilities.
**No deployment work, Dockerfile creation, or cloud infrastructure setup for
the affected modules should proceed until these are reviewed and resolved.**

| PR | Severity | Issue | Affected Module |
|----|----------|-------|-----------------|
| #22 | P0 | Command injection in `get_pid_by_port` | `08_TOOLS_SCRIPTS/status_prober.py` |
| #53 | P0 | SSRF / path traversal | `08_TOOLS_SCRIPTS/blast_agent/tools/scraper_opendata_dortmund.py` |
| #55 | P0 | Command injection | `08_TOOLS_SCRIPTS/status_prober.py` |

Document any work blocked by these issues in `04_REPORTS_AUDITS/`.

---

## 3. Agent Roles and Routing

| Agent | Primary Responsibility | Home Config |
|-------|----------------------|-------------|
| **Jules** | Repository maintenance, PR coordination, manifest updates | `AGENTS/JULES/instructions.md` |
| **Antigravity** | Local PC scanning, scraper execution, tool orchestration | Section 7 below |
| **Codex** | Drive inventory classification, schema enforcement | `03_MANIFESTE_INVENTAR/task_queue.jsonl` |
| **Copilot Cloud Agent** | Code tasks, tests, documentation | `.github/copilot-instructions.md` |
| **Gemini / AI Studio** | Reasoning, generation, creative work | `AGENTS/bridge-config.json` |

**Jules routing shortcuts:**
- ALICE / 3D persona work → `APPS/alice/` and `07_3D_ASSET_LIBRARY/`
- Feed / browser work → `APPS/feednoodle/`
- Prompt library → `APPS/promptdex/`
- Knowledge graph → `APPS/grimm/` and `05_RAG_SOURCE_OF_TRUTH/`
- Dortmund simulation → `APPS/gta-dortmund/`
- Live gateway → `06_GATEWAY_LIVEFEED/`
- Orchestration bridge → `Input/projects/anti-gravity-bridge/`
- Scraper tools → `08_TOOLS_SCRIPTS/blast_agent/`

---

## 4. Security – Non-Negotiable Rules

- **Never** commit credentials, API keys, tokens, passwords, or session cookies.
- Secrets belong in `08_TOOLS_SCRIPTS/blast_agent/.env` (git-ignored) or in
  GitHub Actions secrets.
- MCP server secrets must use the `COPILOT_MCP_` prefix.
- The `.env.template` file documents key names only – never real values.
- Run `git grep -i "api_key\|password\|token"` before committing to catch leaks.

---

## 5. Writing Boundaries

| Area | Permission |
|------|-----------|
| `APPS/{app}/` | Write allowed |
| `Input/projects/` | Write allowed |
| `08_TOOLS_SCRIPTS/` | Write allowed |
| `07_3D_ASSET_LIBRARY/` | Write allowed |
| `AGENTS/` | Write allowed |
| `workspace/` | Write allowed |
| `docs/` | Write allowed |
| `.github/workflows/` | Write allowed |
| `03_MANIFESTE_INVENTAR/` | Write only with explicit task instruction |
| `06_GATEWAY_LIVEFEED/` | Write only with explicit task instruction |
| `04_REPORTS_AUDITS/` | Write only with explicit task instruction |
| `09_ARCHIV_NICHT_ANFASSEN/` | **Read-only** – never modify |
| Any `.env` file | **Never touch** |

---

## 6. Actions Requiring Human Approval

- Archiving or deleting any source repository
- Any paid cloud deployment (Cloud Run, GKE, VMs, managed databases)
- Merging P0 security PRs (#22, #53, #55)
- Importing large binary or data files (> 50 MB) into Git
- Changing GitHub Actions permissions, environments, or secrets
- Removing or rewriting Git history

---

## 7. Antigravity Agent – Local Scanning and Scraper SOPs

The Antigravity agent is authorized to scan and interact with local and online
resources under the following constraints.

### Local PC Scan
- Allowed paths: `Desktop`, `Downloads`, `00_ZENTRALE_INSEL`, `G:\Meine Ablage`
- Excluded: `.git`, `node_modules`, `venv`, `AppData`, `Program Files`, `.ssh`

### Online Resources
- Scrapers are in `08_TOOLS_SCRIPTS/blast_agent/tools/`
- Rate limit Digibib to 1–2 calls per minute
- All credentials load from `08_TOOLS_SCRIPTS/blast_agent/.env`

### Tool Reliability
- If a scraper fails due to HTML changes, diagnose via search and patch
- Use `Path(__file__).resolve()` – never hardcode Windows paths

---

## 8. Connector and MCP Usage

The **GitHub MCP server** is already available to Copilot Cloud Agent with
read access to this repository. Do **not** rebuild GitHub file-browsing,
issue-reading, or PR-management tools in a custom connector.

The ISLAND workspace connector (see `AGENTS/connector/`) provides only
capabilities not covered by GitHub MCP:
- Project catalog queries (`workspace/projects.yaml`)
- Task queue operations (`03_MANIFESTE_INVENTAR/task_queue.jsonl`)
- Health checks for local services
- RAG index search (when available)

For MCP configuration details, see `AGENTS/connector/README.md`.

---

## 9. Definition of Done (per task)

A code task is complete when:
1. All affected tests pass locally and in CI
2. No new flake8 errors are introduced
3. `workspace/projects.yaml` is updated if a project status changed
4. No credentials are present in the diff
5. A summary comment is added to the relevant PR or task queue entry
