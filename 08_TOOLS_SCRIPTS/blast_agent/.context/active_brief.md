# Active Brief: B.L.A.S.T. Agent Scaffolding & Initial Scrapers

## Current Goals

1. Scaffold the directory structure for the local agentic system under `08_TOOLS_SCRIPTS/blast_agent/`.
2. Write the Standard Operating Procedures (SOPs) for the agent run loop and the scraping modules.
3. Write the template credentials file (`.env.template`).
4. Implement the five scraping engines (`scraper_opendata_dortmund.py`, `scraper_digibib.py`, `scraper_scribd.py`, `scraper_statista.py`, `scraper_linkedin.py`) and the local file indexer (`inventory_compiler.py`).
5. Set up `blast_agent.py` CLI interface.

## Target Architecture

* **Layer 1**: Markdown SOPs in `architecture/`.
* **Layer 2**: Reasoning router in `blast_agent.py` and `tools/agent_loop.py`.
* **Layer 3**: Python modules in `tools/` with helper classes for all scraper platforms.

## Constraints

* Store credentials securely in `.env`. Never commit them to Git.
* Strictly enforce rate-limiting of 1-2 calls per minute on Digibib to avoid account banning.
* Ensure exclusions are strictly defined in `inventory_compiler.py` to prevent scanning OS or security-sensitive folders.
* Output intermediate scraped files to `.tmp/`.
