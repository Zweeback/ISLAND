# Anti-Gravity Bridge – Agent Instructions

These rules apply to all agents working inside
`Input/projects/anti-gravity-bridge/`. They override the root `AGENTS.md`
for this project directory.

## Project Summary

A FastAPI orchestrator that connects Unity Editor, headless Blender, and
Meshroom photogrammetry via a DAG-based job execution engine.

**Tech stack:** Python 3.11, FastAPI, Pydantic 2, C# (Unity adapter)
**Tests:** `pytest` from this directory with `PYTHONPATH=.`

## Security Blockers

⛔ **P0 open**: PRs #53 and #55 relate to security issues in modules that
share patterns with this project. Review before adding any network-facing
endpoint or cloud deployment.

## Running Tests

```bash
cd Input/projects/anti-gravity-bridge
PYTHONPATH=. pytest
```

## Writing Rules

- All new modules go in `orchestrator/` or a clearly named sub-package.
- New HTTP endpoints must have a corresponding test in `tests/`.
- `blender/` and `meshroom/` wrappers support dry-run mode via env vars
  (`BLENDER_DRY_RUN=true`, `MESHROOM_DRY_RUN=true`). Tests must not call
  real binaries.
- The Unity C# adapter in `unity/` is editor-only; do not modify it for
  runtime builds.
- Do not hardcode paths. Use `pathlib.Path(__file__).resolve()`.

## Environment Variables (no real values here)

| Variable | Purpose |
|----------|---------|
| `BLENDER_PATH` | Path to Blender binary (default: `blender`) |
| `BLENDER_DRY_RUN` | Set to `true` in tests / CI |
| `MOCK_VRAM_FREE_MB` | Override VRAM reading in tests |
| `MOCK_RAM_FREE_MB` | Override RAM reading in tests |
| `DISABLE_DEFERRED_SCHEDULER` | Disable background scheduler in tests |
| `DEFERRED_MAX_RETRIES` | Override retry limit in tests |
| `ALLOW_OLLAMA_UNLOAD` | Allow Ollama model unloading |

## Out of Scope

- No Dockerfile until P0 security PRs are resolved.
- No cloud deployment without explicit human approval.
- Do not modify `schemas/` JSON files without updating the corresponding tests.
