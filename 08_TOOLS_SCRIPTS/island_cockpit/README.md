# ISLAND Cockpit

Static first cockpit for the ISLAND control plane.

## Purpose

This is the visible layer over the automation work:

- Feed lane: Drive, GitHub, AI Studio and registry signals
- Project lane: APPS and Input/projects candidates
- Agent lane: Codex, Jules, Antigravity, AI Studio
- Task lane: reads `03_MANIFESTE_INVENTAR/task_queue.jsonl`
- Alice lane: 3D asset slot without committing large Drive binaries

## Running Locally

From the repository root:

```powershell
python -m http.server 8787 --bind 127.0.0.1
```

Then open:

```text
http://127.0.0.1:8787/08_TOOLS_SCRIPTS/island_cockpit/
```

## Why No Alice GLB In Git

The real Alice assets are already in Drive/local inventory and can be large. This cockpit does not blindly copy binaries into Git. It provides a local file picker and registry slot first. Production asset loading should use `drive_inventory_registry.jsonl` or Git LFS after review.

## Next Steps

1. Wire the cockpit to `source_registry.jsonl` and `drive_inventory_registry.jsonl` when those files exist.
2. Add GitHub Pages or another static host for mobile access.
3. Add task status updates from Jules/Antigravity PRs and issues.
