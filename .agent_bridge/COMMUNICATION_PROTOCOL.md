
## Automated Polling and Response Loop (Added 2026-07-06)
The Agent Bridge now supports full asynchronous automation to preserve context limits and Codex credits.

### Three-Tier Automation Stack
1. **Local Watcher (`watch-bridge.ps1`):** A PowerShell script running locally monitors the `.agent_bridge/inbox` and `.agent_bridge/state` directories. It tracks file cursors (`bridge_cursor.json`) and writes status updates (`bridge_watch_status.json`).
2. **Codex Heartbeat:** The upstream LLM/App periodically polls the state files and watcher outputs to understand if new tasks have been registered.
3. **Agent Workflows:** Antigravity (local Windows) and Jules (remote Linux/Repo) drop `.json` or `.md` artifacts into the `inbox/` indicating task completion or failure. The Heartbeat detects these, formulates the next context-aware prompt, and drops it into `outbox/`.

### Constraints for Jules
Jules operates entirely headless without local Windows access. When Jules writes documentation or responds to a task that requires local verification, Jules **must** explicitly tag the response or document with `sandbox_limited: true`. Jules relies strictly on artifacts produced by Antigravity (e.g., `antigravity-runtime-status.json`) to determine the success of local builds.
