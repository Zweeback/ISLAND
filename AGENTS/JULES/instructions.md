# Jules Operating Instructions

Jules coordinates ISLAND as the primary workspace. It should use the repo ledger before assuming where an app lives.

## Startup

1. Read `AGENTS/JULES/config.json`.
2. Read `03_MANIFESTE_INVENTAR/repos_merged.jsonl`.
3. Discover app homes under `APPS/`.
4. Treat `05_RAG_SOURCE_OF_TRUTH/engine/` as executable RAG code and `05_RAG_SOURCE_OF_TRUTH/indexes/` as index/data material.
5. Treat `09_ARCHIV_NICHT_ANFASSEN/imported-repos/` as reference-only unless a task explicitly promotes one of those repos into an active lane.

## Routing

- ALICE/persona/3D work: `APPS/alice/` and `07_3D_ASSET_LIBRARY/`.
- Feed/browser work: `APPS/feednoodle/`.
- Prompt library work: `APPS/promptdex/`.
- Knowledge graph work: `APPS/grimm/` and RAG source-of-truth folders.
- Dortmund simulation work: `APPS/gta-dortmund/`.
- Gateway/live-feed work: `06_GATEWAY_LIVEFEED/`.

## Safety

Do not delete, archive, or rewrite source repositories as part of normal routing. The consolidation ledger marks sources as preserved. Archive/deletion requires a separate explicit request.
