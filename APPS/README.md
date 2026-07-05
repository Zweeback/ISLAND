# ISLAND Apps Directory

Consolidated workspace for active applications managed from ISLAND and coordinated by Jules / Gemini / AI Studio.

## Target Structure

| Path | Sources | Purpose |
| --- | --- | --- |
| `APPS/alice/` | `Zweeback/alice`, `Zweeback/3-d-persona` | ALICE persona and 3D character work. |
| `APPS/feednoodle/` | `Zweeback/feednoodle` | Browser/feed workspace. |
| `APPS/promptdex/` | `Zweeback/promptdex` | Prompt library and command surface. |
| `APPS/grimm/` | `Zweeback/GRIMM` | Knowledge graph and narrative/semantic tooling. |
| `APPS/gta-dortmund/` | `Zweeback/GTA`, `Zweeback/DORTMUND-GTA` | Dortmund simulation sandbox. |
| `APPS/shared/` | ISLAND-native | Shared utilities, configs, and integration glue. |

## Import Policy

Each app folder must keep an `ORIGINAL_REPO.md` file that records source repositories, visibility, default branch, import date, and current import status. The canonical machine-readable ledger is `03_MANIFESTE_INVENTAR/repos_merged.jsonl`.

Source repositories are not deleted or archived by this consolidation. They remain available as references until a later explicit archive step is approved.

## Current Status

This pass creates the ordered homes and repo ledger. Full source-tree copying is intentionally recorded per source in the ledger so private, empty, or connector-limited repositories are not represented as fully copied when they are not.
