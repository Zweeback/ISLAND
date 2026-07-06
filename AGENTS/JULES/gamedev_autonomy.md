# Autonomous GameDev Coordination

Purpose: coordinate agents so ISLAND can grow into an autonomous gamedev system that combines app repos, RSS/source feeds, RAG memory, and game/simulation targets without losing control of safety or direction.

## Core Roles

| Role | Home | Responsibility |
| --- | --- | --- |
| Jules Orchestrator | `AGENTS/JULES/` | Plans work, assigns lanes, checks ledgers, and writes status. |
| OpenClaw Gateway | `06_GATEWAY_LIVEFEED/openclaw/` | Optional bridge for cross-machine/live-feed/event routing. |
| Source Ingest | `01_INGEST_INBOX/` and `06_GATEWAY_LIVEFEED/` | Collect RSS, links, datasets, logs, and incoming app material. |
| RAG Memory | `05_RAG_SOURCE_OF_TRUTH/` | Stores reviewed knowledge, indexes, and retrieval context. |
| GRIMM | `APPS/grimm/` | Builds semantic/knowledge graph views of sources and game concepts. |
| GTA Dortmund | `APPS/gta-dortmund/` | First game/simulation target for autonomous build loops. |
| ALICE | `APPS/alice/` and `07_3D_ASSET_LIBRARY/` | Character/persona/3D asset lane. |
| PromptDex | `APPS/promptdex/` | Reusable prompts, agent tasks, and command recipes. |

## Loop

1. Intake: collect source material from RSS, Drive exports, GitHub repos, datasets, and local drops.
2. Normalize: write summaries and metadata into manifests; keep raw files in ingest/source lanes.
3. Retrieve: index reviewed material into RAG and GRIMM.
4. Plan: Jules creates small game-dev tasks with clear acceptance checks.
5. Build: agents work inside the relevant app lane.
6. Verify: run tests, lint, smoke checks, and asset inspections where available.
7. Record: update manifests, status notes, and next tasks.

## Autonomy Boundaries

Agents may propose and prepare changes, but these actions require explicit approval or a PR review before becoming durable production state:

- deleting or archiving source repositories
- spending cloud money
- publishing public artifacts
- running unattended commands on a new machine
- using credentials, cookies, or private APIs
- changing security-sensitive gateway behavior

## First GameDev Target

Use `APPS/gta-dortmund/` as the first autonomous build target. The first system goal is not a full game; it is a stable loop that can:

- ingest Dortmund/open-data/source feeds
- extract entities, locations, mechanics, and assets
- store them in RAG/GRIMM
- generate small simulation tasks
- validate that outputs are recorded and replayable

## Status Files

Suggested status files for future implementation:

- `06_GATEWAY_LIVEFEED/source_feeds.jsonl`
- `03_MANIFESTE_INVENTAR/agent_workflows.jsonl`
- `04_REPORTS_AUDITS/autonomy_status.md`
