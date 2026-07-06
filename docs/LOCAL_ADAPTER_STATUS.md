# Local Adapter Status
> **Note:** `sandbox_limited: true`
> As the Jules agent operates in an isolated Linux container, I cannot directly verify the live Windows runtime or local services. The following status is reported based on the Agent Bridge state and documentation.

## Current State
- **Runtime:** `Adapter-v2` is confirmed to be running locally.
- **Endpoint:** The service is available at `http://localhost:8080`.
- **LLM Provider:** Local Ollama instance is active and serving the `gemma4:latest` model.
- **Verification:** The `/chat` endpoint with `provider=ollama` has been successfully verified by Antigravity/Codex.

## Agent Responsibilities
- **Antigravity:** Responsible for direct local execution, stability, and modifications to the local Windows runtime environment (e.g., `SovereignCloudRunAdapter`).
- **Jules:** Responsible strictly for repository maintenance, documentation, and logic patching within the repository bounds. Jules must rely on `.agent_bridge/outbox` signals to understand local state.
