# ISLAND Connector – Agent and MCP Integration

This directory contains configuration templates and documentation for
integrating AI tools and connectors with the ISLAND workspace.

## What Lives Here

| File / Dir | Purpose |
|-----------|---------|
| `copilot-mcp.template.json` | Template for GitHub Copilot Cloud Agent MCP server config |
| `README.md` | This file |

## What Does NOT Live Here

The **effective MCP configuration** for GitHub Copilot Cloud Agent is **not
activated by committing a JSON file to this directory**. It must be entered in:

> **GitHub Repository Settings → Copilot → MCP servers**

This directory serves as the versionable documentation and template source.

---

## GitHub MCP Server – Already Available

GitHub Copilot Cloud Agent has a **built-in GitHub MCP server** with read
access to this repository by default. It can already:

- Browse files and directories
- Read issues and pull requests
- Search code

**Do not rebuild these capabilities in a custom ISLAND connector.**

---

## ISLAND Workspace Connector – What to Build

The ISLAND connector should only expose capabilities that the GitHub MCP server
does **not** provide:

| Tool | Description |
|------|-------------|
| `get_project` | Look up a project entry from `workspace/projects.yaml` by ID |
| `list_projects` | List all projects filtered by status, type, or deployable flag |
| `get_task` | Retrieve a task from `03_MANIFESTE_INVENTAR/task_queue.jsonl` |
| `health_check` | Query the status of a local service (bridge, scraper, etc.) |
| `search_manifest` | Full-text search over `03_MANIFESTE_INVENTAR/island_manifest.jsonl` |

All tools should be **read-only** unless a specific write operation is
explicitly approved and documented in `policies/`.

---

## Registering the MCP Server (Copilot Cloud Agent)

1. **Create the MCP server** that implements the tools above. A minimal
   FastAPI-based server can be found at
   `Input/projects/anti-gravity-bridge/orchestrator/main.py` as a reference.

2. **Deploy the server** to a reachable endpoint (e.g., a local tunnel or
   a Cloud Run service – but only after P0 security PRs #22, #53, #55 are
   resolved).

3. **Register secrets** in GitHub:
   - Go to **Repository Settings → Environments → copilot**
   - Add secrets with the `COPILOT_MCP_` prefix (required by GitHub):
     - `COPILOT_MCP_ISLAND_TOKEN` – bearer token for the server

4. **Enter the MCP configuration** in
   **Repository Settings → Copilot → MCP servers**
   using the JSON from `copilot-mcp.template.json` as a starting point,
   substituting real values.

---

## VS Code / Local Development

For local VS Code or Codespaces usage, copy `copilot-mcp.template.json` and
adapt it for your local setup. Store it in `.vscode/mcp.json` (git-ignored).

---

## Security Policy

- All MCP tools are **read-only by default**.
- Write tools require an explicit entry in `policies/write-boundaries.yaml`
  (not yet created – add when needed).
- The `COPILOT_MCP_` prefix is mandatory for all MCP-related secrets.
- Never grant wildcard tool access. List each allowed tool explicitly.
- GitHub's built-in Playwright access is limited to `localhost`/`127.0.0.1` –
  do not rely on it for external resource fetching.
