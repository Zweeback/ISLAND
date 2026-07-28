# Blast Agent – Agent Instructions

These rules apply to all agents working inside
`08_TOOLS_SCRIPTS/blast_agent/`. They override the root `AGENTS.md`
for this project directory.

## Project Summary

A Python scraper and automation toolkit covering:
- OpenData Dortmund (public API)
- Digibib / hbz library catalog
- Scribd, Statista (authenticated scrapers)
- LinkedIn (`li_at` session cookie)
- Local LLM bridge (Ollama / xAI)

**Tech stack:** Python 3.11, httpx, pydantic, requests/playwright
**Tests:** `PYTHONPATH=. pytest` from the `blast_agent/` directory

## ⛔ Security Blockers

**PR #53** – SSRF / path traversal in `tools/scraper_opendata_dortmund.py`
**PR #55** – Command injection in `status_prober.py` (sibling module)

Both are **P0**. Do **not** expose any scraper endpoint publicly until these
are patched and merged.

## Running Tests

```bash
cd 08_TOOLS_SCRIPTS/blast_agent
PYTHONPATH=. pytest
```

## Credentials – Critical Rules

- Credentials are loaded **only** from `08_TOOLS_SCRIPTS/blast_agent/.env`
  (git-ignored).
- The `.env.template` contains key names only – **never** real values.
- **Never** print, log, or commit any credential value.
- Session cookies (`LINKEDIN_COOKIE_LI_AT`, `SCRIBD_COOKIE`, etc.) are
  sensitive. Treat them as secrets.

## Rate Limiting

| Service | Limit |
|---------|-------|
| Digibib | 1–2 calls / minute |
| Statista | session-dependent – be conservative |
| LinkedIn | Use sparingly; excessive scraping violates ToS |

## Writing Rules

- New scrapers go in `tools/` and must have a corresponding test file
  `tools/test_{scraper_name}.py` or `tests/test_{scraper_name}.py`.
- Use `pathlib.Path(__file__).resolve()` – no hardcoded paths.
- All network calls must be wrapped in try/except with informative logging.
- Playwright-based scrapers must support a `headless=True` mode for CI.

## Out of Scope

- No Docker container for this module until P0 PRs are resolved.
- No cloud deployment without explicit human approval.
- Do not import real credentials into any test fixture.
