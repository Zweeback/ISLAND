# ISLAND Cleanup and Consolidation Roadmap

## Goal

Move from fragmented repositories toward one ordered ISLAND workspace with stable app homes, a manifest ledger, and Jules routing.

## Phase 1: Structure and Ledger

- [x] Create active app homes under `APPS/`.
- [x] Create RAG engine/index homes under `05_RAG_SOURCE_OF_TRUTH/`.
- [x] Create reference homes under `09_ARCHIV_NICHT_ANFASSEN/imported-repos/`.
- [x] Add `03_MANIFESTE_INVENTAR/repos_merged.jsonl`.
- [x] Add Jules coordination docs.

## Phase 2: Full Source Import

- [ ] Copy full source trees where connector or local git access is available.
- [ ] Exclude nested `.git`, credentials, build caches, dependency folders, and generated artifacts.
- [ ] Update each `ORIGINAL_REPO.md` from registered to copied when content has actually landed.
- [ ] Keep large/binary RAG indexes reviewed before adding them to Git.

## Phase 3: Reconcile Open Jules PRs

- [ ] Review open security fixes first: #22, #53, #55, #56 if reopened.
- [ ] Review consolidation-adjacent PR #59 before merging overlapping ALICE/test changes.
- [ ] Review performance/test PRs for duplication before merging.

## Phase 4: Archive Decision

- [ ] Decide which source repositories should be archived.
- [ ] Add archive notices to source repos only after explicit approval.
- [ ] Do not delete any source repository.

## OpenClaw Gateway

OpenClaw is treated as an optional gateway candidate, not a required dependency for consolidation. See `06_GATEWAY_LIVEFEED/openclaw_gateway.md`.
