# GitHub Copilot Instructions – ISLAND Repository

This file sets repository-wide rules for GitHub Copilot (inline suggestions,
chat, code review, and cloud agent tasks). Project-specific rules are in each
project's own `AGENTS.md`.

## Repository Identity

ISLAND is a **consolidation monorepo**. It gathers multiple personal projects,
tools, agents, and data sources into one ordered workspace. It is **not** a
production platform. Most `APPS/` folders are placeholders awaiting code import
from their original repositories.

## Security – Non-Negotiable Rules

- **NEVER** commit credentials, API keys, tokens, passwords, or session cookies.
  All secrets belong in `08_TOOLS_SCRIPTS/blast_agent/.env` (git-ignored) or in
  GitHub Actions secrets / the `copilot` environment.
- **NEVER** read or output the contents of any `.env` file.
- The `.env.template` file documents key names only – never real values.
- MCP server secrets must use the `COPILOT_MCP_` prefix convention.

## P0 Security Blockers (as of 2026-07-28)

The following open PRs contain security fixes and **must be reviewed before any
deployment work proceeds**:

| PR | Issue | Status |
|----|-------|--------|
| #22 | Command injection in `get_pid_by_port` (`status_prober.py`) | Open |
| #53 | SSRF / path traversal in OpenData Dortmund scraper | Open |
| #55 | Command injection in `status_prober.py` | Open |

No Dockerfile, cloud resource, or deployment pipeline for the affected modules
should be created until these are resolved.

## Workspace Structure

| Area | Purpose |
|------|---------|
| `workspace/projects.yaml` | Canonical project catalog – single source of truth |
| `03_MANIFESTE_INVENTAR/` | Machine-readable manifests (repos_merged, task_queue, island_manifest) |
| `APPS/{app}/` | Placeholder homes for apps not yet imported |
| `Input/projects/` | Projects with actual code present |
| `08_TOOLS_SCRIPTS/` | Active tools (blast_agent, island_cockpit, etc.) |
| `05_RAG_SOURCE_OF_TRUTH/` | RAG data – not yet imported from source repos |
| `09_ARCHIV_NICHT_ANFASSEN/` | Reference archive – do not modify |
| `07_3D_ASSET_LIBRARY/` | 3D assets and viewer |

## Writing Boundaries

- **Read freely**: any file in the repository.
- **Write allowed**: `APPS/{app}/`, `Input/projects/`, `08_TOOLS_SCRIPTS/`,
  `07_3D_ASSET_LIBRARY/`, `AGENTS/`, `workspace/`, `docs/`, root config files,
  `.github/workflows/`.
- **Write restricted** (require explicit task instruction):
  `03_MANIFESTE_INVENTAR/`, `06_GATEWAY_LIVEFEED/`, `04_REPORTS_AUDITS/`.
- **Do not touch**: `09_ARCHIV_NICHT_ANFASSEN/`, `.env` files, any file
  containing real credentials.

## Actions Requiring Human Approval

- Archiving or deleting any source repository.
- Initiating any paid cloud deployment (Cloud Run, GKE, VMs).
- Merging security-related PRs (P0 list above).
- Importing large binary or data files into Git.
- Changing GitHub Actions permissions or secrets.

## Context Efficiency

The GitHub MCP server is **already available** to Copilot Cloud Agent with
read access to this repository. Do **not** rebuild file-browsing or
issue-reading tools in a custom connector. Only build workspace-specific
capabilities that GitHub MCP does not provide (project catalog queries, health
checks, RAG search, task queue operations).

## Coding Standards

- Python: PEP 8, dynamic path resolution via `pathlib.Path(__file__).resolve()`.
- No hardcoded Windows paths (`C:\Users\...`).
- All new Python modules need at least one test in the project's `tests/` folder.
- JSON/YAML files must be valid and schema-compliant where a schema exists.

## Related Files

- `AGENTS.md` – Agent governance and routing
- `workspace/projects.yaml` – Project catalog
- `AGENTS/connector/README.md` – Connector and MCP setup
