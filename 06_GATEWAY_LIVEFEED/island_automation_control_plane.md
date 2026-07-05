# ISLAND Automation Control Plane

Generated: 2026-07-05

## Core Decision

The Drive inventory CSV is not the product. It is the source material for automation.

ISLAND must become the control plane that tells every agent:

- what exists
- where it came from
- who may touch it
- what the next action is
- what must stay human-approved

## Authority Model

```text
Master truth:        GitHub / Zweeback/ISLAND
Drive truth:         existing Drive inventory CSV + Drive metadata
Local coordinator:   Codex
Cloud coordinator:   Jules
Workbench:           Antigravity
Prototype source:    AI Studio / Gemini exports
Optional later:      OpenClaw adapter, not required now
```

## No More Blind Sync

Git, Drive, AI Studio, Jules, Antigravity and Codex do not automatically share state.

The fix is not another raw CSV export. The fix is a registry and task routing layer inside ISLAND.

## Required ISLAND Registries

These files should live in `03_MANIFESTE_INVENTAR/`:

```text
source_registry.jsonl
drive_inventory_registry.jsonl
agent_registry.jsonl
interface_registry.jsonl
task_queue.jsonl
handoff_log.jsonl
risk_register.jsonl
metrics_registry.jsonl
artifact_registry.jsonl
ai_studio_projects.jsonl
```

## Agent Roles

Codex:

- local scanner and registry builder
- reads local CSVs and repo state
- writes schemas, validators, reports and safe patches
- uses subagents for bounded analysis

Jules:

- primary GitHub cloud coordinator
- works through GitHub Issues and PRs
- handles code, docs, tests, security PR cleanup
- must not need local Drive secrets

Antigravity:

- multi-agent workbench
- maps AI Studio projects to app candidates
- decomposes game-dev workflows
- prepares app/prototype/export packets

AI Studio:

- prototype source only
- not the master code store
- every app must be exported and registered before becoming an ISLAND app

Drive:

- asset, document and archive source
- large files stay linked, not blindly committed
- CSV is used to classify and prioritize

## Trigger Rules

Use Jules when:

```text
label: agent:jules
task: bounded GitHub code/test/docs/security change
input: repo paths and acceptance criteria
output: branch or PR
no local Drive secret required
```

Use Antigravity when:

```text
label: agent:antigravity
task: multi-agent planning, app export, AI Studio mapping, game-dev workflow
input: registry rows, app folders, docs
output: design packet, export checklist, task breakdown
```

Use Codex subagents when:

```text
task: local analysis, CSV classification, registry validation, PR triage
input: local files or GitHub metadata
output: report, JSONL proposal, schema finding
```

Human approval required for:

```text
repo archive/delete
copying big Drive assets into Git
secrets, .env, API keys, OAuth changes
real Unity/Blender/Unreal project modification
merging security-sensitive PRs
granting agent permissions
```

## First Automation Loop

```text
1. Codex reads Drive inventory CSV.
2. Codex classifies rows into drive_inventory_registry.jsonl.
3. Codex writes source_registry.jsonl entries for important assets/docs/repos.
4. Antigravity maps AI Studio/project rows to APPS candidates.
5. Jules receives GitHub Issues generated from task_queue.jsonl.
6. Jules opens PRs.
7. Codex validates PRs and registry consistency.
8. Human approves risky actions.
```

## P0 Tasks

```text
P0-1: Create registry schemas and validators.
P0-2: Classify Drive inventory CSV into registry rows.
P0-3: Add agent_registry and interface_registry.
P0-4: Create Jules task queue for existing security PRs.
P0-5: Create Antigravity task queue for AI Studio project mapping.
```
