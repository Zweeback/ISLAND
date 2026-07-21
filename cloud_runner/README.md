# Free-only Multi-LLM Cloud Runner

This runner is designed for accounts with no payment method attached. It fails closed: paid providers are disabled unless `ALLOW_PAID_PROVIDERS=true` is explicitly set.

## Default fallback order

1. `github` — GitHub Models using the workflow's short-lived `GITHUB_TOKEN` and included free quota.
2. `gemini` — Gemini Developer API free tier using `GEMINI_API_KEY`.
3. `custom` — an optional user-controlled OpenAI-compatible endpoint.

When a provider returns quota exhaustion (`429`), authentication failure, a transient server error, or no usable response, the router records the attempt and moves to the next provider in the same workflow job. This avoids starting another GitHub Actions run merely to switch models.

## Cost controls

- `ALLOW_PAID_PROVIDERS` is hard-coded to `false` in the workflow.
- OpenAI and xAI adapters exist in the router but remain blocked by policy.
- Without a valid payment method, GitHub Models blocks requests after the included quota rather than charging.
- Gemini must use a Free Tier project/API key. Do not attach a paid billing project to that key.
- No secret is printed by the router.

## Required repository settings

Enable GitHub Models for the repository under **Settings → Models**.

Add this repository secret if Gemini fallback is wanted:

- `GEMINI_API_KEY`

Optional custom endpoint settings:

- Secret `CUSTOM_LLM_BASE_URL`
- Secret `CUSTOM_LLM_API_KEY`
- Variable `CUSTOM_LLM_MODEL`

Optional model variables:

- `GITHUB_MODEL` (default `openai/gpt-4.1`)
- `GEMINI_MODEL` (default `gemini-3.5-flash`)

## Run

Open **Actions → Free Multi-LLM Cloud Runner → Run workflow** and provide a prompt. The result and all provider attempts appear in the job summary.

## Failure behavior

The workflow returns a non-zero status only after all configured providers fail. The JSON result distinguishes `quota_exhausted`, `auth`, `network`, `timeout`, `request`, `blocked`, and `all_failed` conditions.
