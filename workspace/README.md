# Workspace Catalog

The `workspace/` directory contains the machine-readable project catalog for
the ISLAND monorepo. It is the single source of truth for all agents, CI
pipelines, and connector tools.

## Files

| File | Purpose |
|------|---------|
| `projects.yaml` | Complete list of all projects (active, placeholder, archived) |
| `projects.schema.json` | JSON Schema – CI validates `projects.yaml` against this |

## How to Use

### Find a project's canonical path
```python
import yaml, pathlib
catalog = yaml.safe_load(pathlib.Path("workspace/projects.yaml").read_text())
projects = {p["id"]: p for p in catalog["projects"]}
print(projects["anti-gravity-bridge"]["path"])
# → Input/projects/anti-gravity-bridge
```

### Check if a project is deployable
```python
project = projects["gta-dortmund"]
print(project["deployable"])  # → False (placeholder, no code yet)
```

### List all active / canonical projects with tests
```python
runnable = [
    p for p in catalog["projects"]
    if p["status"] in ("canonical", "active") and p.get("test_command")
]
```

## Status Definitions

| Status | Meaning |
|--------|---------|
| `canonical` | Primary copy, code present, tests run in CI |
| `active` | Usable, may not be primary |
| `experimental` | In development, may be unstable |
| `placeholder` | Directory created, source code not yet imported |
| `data-only` | No runnable code, contains only data or binary assets |
| `docs-only` | Documentation files only |
| `archived` | Reference copy, do not modify |
| `reference-only` | External reference, read-only |
| `unknown` | Not yet classified |

## Adding a New Project

1. Add an entry to `projects.yaml` following the existing pattern.
2. Run `python workspace/validate.py` locally to check schema and paths.
3. Commit – CI (`workspace-validate.yml`) will re-validate automatically.

## Updating an Existing Project

When a placeholder receives actual code from its source repository, update:
- `status`: from `placeholder` to `canonical` or `active`
- `language` and `framework`: add detected stack
- `install_command` and `test_command`: add verified commands
- `source_status`: from `unavailable` / `pending_import` to `present`
- `deployable`: set to `true` only after tests pass and security PRs are resolved

## CI Integration

The workflow `.github/workflows/workspace-validate.yml` runs on every push and
pull request. It checks:
- YAML syntax of `projects.yaml`
- Schema compliance against `projects.schema.json`
- Existence of every catalogued `path` in the repository
- No duplicate project `id` values
- No forbidden `status` values
- Basic secret pattern scan on template and config files
