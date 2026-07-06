# ISLAND Agent Architecture

Status: consolidation branch
Primary orchestrator: Jules / Gemini / AI Studio

## Structure

```text
AGENTS/
  JULES/
    config.json
    instructions.md
APPS/
  alice/
  feednoodle/
  promptdex/
  grimm/
  gta-dortmund/
  shared/
05_RAG_SOURCE_OF_TRUTH/
  engine/
  indexes/
06_GATEWAY_LIVEFEED/
  openclaw_gateway.md
09_ARCHIV_NICHT_ANFASSEN/
  imported-repos/
```

## Agent Flow

1. User request arrives in ISLAND.
2. Jules reads the ledger in `03_MANIFESTE_INVENTAR/repos_merged.jsonl`.
3. Jules routes to the correct app home, RAG home, or reference archive.
4. App-specific work remains under `APPS/`; shared RAG material remains under `05_RAG_SOURCE_OF_TRUTH/`.
5. Gateway integrations, including OpenClaw if needed later, live under `06_GATEWAY_LIVEFEED/`.

## Source Preservation

All source repositories remain preserved. This branch does not delete, archive, or disable any source repository.
