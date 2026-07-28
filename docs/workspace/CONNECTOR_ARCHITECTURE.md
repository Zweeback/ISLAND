# Connector Architecture – ISLAND Workspace

**Status:** Planning / Template Phase
**Blocker:** P0 security PRs #22, #53, #55 must be resolved before any server
is deployed.

---

## Overview

The ISLAND connector provides AI tools with structured, workspace-aware access
to project metadata, task queues, and health information. It complements the
GitHub MCP server (already built into Copilot Cloud Agent) by exposing
capabilities specific to the ISLAND monorepo.

```
┌─────────────────────────────────────────────────────────────┐
│              AI Tool / Copilot Cloud Agent                   │
│                                                              │
│  Built-in GitHub MCP          ISLAND Workspace MCP          │
│  ─────────────────────        ─────────────────────         │
│  • read files                 • list_projects                │
│  • read issues/PRs            • get_project                  │
│  • search code                • get_task                     │
│  (do not rebuild these)       • search_manifest              │
│                               • health_check                 │
└───────────────┬───────────────────────┬─────────────────────┘
                │                       │
                ▼                       ▼
        GitHub API               ISLAND MCP Server
                                  (not yet deployed)
                                        │
                          ┌─────────────┼──────────────┐
                          ▼             ▼              ▼
                  workspace/      03_MANIFESTE_   Local services
                  projects.yaml   INVENTAR/       (bridge, prober)
```

---

## Components

### 1. GitHub MCP Server (Built-in – Already Active)

Provided by GitHub. Read access to this repository by default. No custom
setup required.

**Available to Copilot Cloud Agent automatically:**
- File and directory browsing
- Issue and PR reading
- Code search

**Not available (must be enabled separately in Repository Settings):**
- Write access (create/edit files, open PRs)

### 2. ISLAND Workspace MCP Server (Planned)

A small HTTP server exposing workspace-specific read-only tools.

**Reference implementation base:** `Input/projects/anti-gravity-bridge/orchestrator/main.py`
(FastAPI, already in the repo – can be extended)

**Tools:**

| Tool | Input | Output | Source |
|------|-------|--------|--------|
| `get_project` | `id: str` | Project entry | `workspace/projects.yaml` |
| `list_projects` | `status?, type?, deployable?` | Filtered list | `workspace/projects.yaml` |
| `get_task` | `task_id: str` | Task entry | `03_MANIFESTE_INVENTAR/task_queue.jsonl` |
| `search_manifest` | `query: str` | Matching entries | `03_MANIFESTE_INVENTAR/island_manifest.jsonl` |
| `health_check` | `service_id: str` | Service status | `06_GATEWAY_LIVEFEED/service_status.jsonl` |

**All tools are read-only.** Write tools require explicit approval and
documentation.

### 3. OpenAPI Specification (Planned)

A formal `openapi/workspace-api.yaml` can be derived from the MCP tool
definitions above. This would allow:
- Non-MCP clients to call the API via HTTP
- Automated testing of the API contract
- Auto-generated client SDKs

**Not yet created.** Create once the MCP server has stable tool definitions.

---

## Configuration Layers

| Layer | File | Scope |
|-------|------|-------|
| Copilot repository rules | `.github/copilot-instructions.md` | All Copilot sessions |
| Agent governance | `AGENTS.md` | All agents |
| MCP server config template | `AGENTS/connector/copilot-mcp.template.json` | Documentation |
| **Effective MCP config** | GitHub Repository Settings → Copilot → MCP servers | Runtime |
| Project catalog | `workspace/projects.yaml` | All tools |
| Project catalog schema | `workspace/projects.schema.json` | CI validation |

---

## Activation Checklist

The connector is **not active**. Complete these steps (in order) to activate:

- [ ] Resolve P0 security PRs #22, #53, #55
- [ ] Decide on hosting (local tunnel vs. Cloud Run – requires separate decision)
- [ ] Implement MCP tools based on `workspace/projects.yaml` and
      `03_MANIFESTE_INVENTAR/task_queue.jsonl`
- [ ] Write tests in `AGENTS/connector/tests/`
- [ ] Deploy server to a reachable endpoint
- [ ] Add `COPILOT_MCP_ISLAND_TOKEN` secret in GitHub
      (Settings → Environments → copilot)
- [ ] Paste adapted `copilot-mcp.template.json` into
      GitHub → Repository Settings → Copilot → MCP servers
- [ ] Verify tools appear in Copilot session logs
- [ ] Document tool allowlist and write-boundary policy

---

## Security Model

- **Read-only by default.** All tools only read from files in this repository
  or from local service health endpoints.
- **No GitHub tool duplication.** The GitHub MCP server already handles
  repository reads, issues, and PRs.
- **COPILOT_MCP_ prefix.** All secrets for Copilot MCP must use this prefix
  (GitHub requirement).
- **Explicit tool allowlist.** No wildcard grants. Each tool is named
  individually in the configuration.
- **Local-only scope until P0 resolved.** No internet-facing deployment before
  security issues are fixed.

---

## Cloud Deployment Decision

**Not decided yet.** The current phase is planning only.

Options to evaluate once P0 PRs are resolved:

| Option | Cost | Complexity | Connector-ready |
|--------|------|-----------|----------------|
| Local tunnel (ngrok/cloudflared) | Free | Low | Yes, for dev |
| GitHub Codespaces (forwarded port) | Included | Low | Yes, for Copilot sessions |
| Cloud Run (GCP) | Pay-per-use | Medium | Yes, for production |
| Static file serving | Free | Very low | Read-only, limited |

**Recommendation:** Start with Codespaces forwarded port during development.
Escalate to Cloud Run only when there is a demonstrated need and after security
review.
