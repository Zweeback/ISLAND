# Zentrale Insel: Gap Analysis & Unified Live-Feed Architecture

This document maps the user's vision (unifying local/online resources, GitHub, Firebase, Drive Takeout, and 3D Alice into a live development feed) against the current state of the repository.

## 1. Current State (Was schon da ist)

* **Directory Structure**: The foundational folders (`01_INGEST_INBOX`, `03_MANIFESTE_INVENTAR`, `06_GATEWAY_LIVEFEED`, `07_3D_ASSET_LIBRARY`, etc.) exist.
* **B.L.A.S.T. Agent Scaffolding**: `blast_agent.py` and the tools directory exist. The script executes and paths are dynamic. The `opendata_dortmund` scraper is functional.
* **Live Feed Schema**: `LIVE_STATUS_CONTRACT.md` dictates strict JSONL schemas (`service_status.jsonl`) for tracking system components (processes, ports, healthchecks).
* **Tracked Services**: Currently `service_status.jsonl` tracks `gateway_openclaw`, `rag_retriever`, `tts_speaker`, and `alice_3d_frontend` (all currently offline).
* **Workspace Map**: `Workspace.md` maps out 4 phases, identifying Firebase deployments and GitHub tokens, as well as local indexing strategies.

## 2. Missing Components (Was noch fehlt)

To realize the vision of a "unified development feed" feeding into a "3D Alice game dev environment," the following components are missing:

* **Drive Takeout Indexer**: There is currently no script in `08_TOOLS_SCRIPTS/blast_agent/tools/` specifically designed to safely parse a 500GB Drive Takeout archive into `03_MANIFESTE_INVENTAR` without overwhelming local storage.
* **Firebase & GitHub Telemetry Feed**: While Firebase MCP is mentioned in `Workspace.md`, there is no active script pulling deployment/commit statuses from Firebase or GitHub into the `service_status.jsonl` live feed.
* **3D Alice Asset Bridge**: `alice_3d_frontend` is in the `service_status.jsonl` as offline, but there is no pipeline moving parsed data from `03_MANIFESTE_INVENTAR` into `07_3D_ASSET_LIBRARY` for the 3D game engine.
* **Unified Feed Aggregator**: A script to compile the individual scraper outputs, the local inventory, and the service statuses into one central "Development Feed" format.

## 3. Architecture Proposal (Der Architektur-Plan)

To bridge the gap between the current state and the unified vision:

### Step A: Implement the Takeout / Local Indexer
Create an incremental script (`inventory_compiler.py`) that specifically targets the `G:\Meine Ablage` (Google Drive mount). It should output lightweight JSON manifests (file path, type, category) into `03_MANIFESTE_INVENTAR` rather than copying large files.

### Step B: Build the GitHub/Firebase Status Prober
Create a script (e.g., `status_prober.py`) that runs periodically. It checks GitHub for recent commits and Firebase for deployment statuses, and writes these states as telemetry events into `06_GATEWAY_LIVEFEED/service_status.jsonl` adhering strictly to the `LIVE_STATUS_CONTRACT.md`.

### Step C: The "3D Alice" Asset Bridge
Create a transformation script that reads the parsed Takeout manifests from `03_MANIFESTE_INVENTAR` and translates them into a game-ready asset format (JSON/Markdown metadata) in `07_3D_ASSET_LIBRARY`. This allows the 3D Alice frontend to read and display the inventory.

### Step D: The Master "Development Feed" UI/Aggregator
The existing `service_status.jsonl` is a system feed. We need a parser (potentially part of the Firebase deployment or a local HTML dashboard) that reads this JSONL and renders a human-readable "Unified Development Feed" showing live project health, AI instance states, and recent data ingestions.