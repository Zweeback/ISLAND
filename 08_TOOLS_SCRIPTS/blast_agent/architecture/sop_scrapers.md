# SOP: Data Ingestion & Scraper Operations (sop_scrapers.md)

This Standard Operating Procedure (SOP) defines the operational guidelines, rate limits, and safety measures for all scraping modules under `tools/`.

---

## 1. General Principles

* **Ethical Harvesting**: All scrapers must respect target website rate limits. Never flood servers.
* **Credential Protection**: Credentials (passwords, PINs, session cookies) must only be read from `.env` or system environment variables. Never hardcode them.
* **Output Format**: All scraped outputs must be saved to `.tmp/` as JSON or raw text before being processed and moved to `01_INGEST_INBOX/`.

---

## 2. Platform-Specific Guidelines

### OpenData Dortmund

* **Mechanism**: REST HTTP requests against `open-data.dortmund.de/api/explore/v2.1`.
* **Rate Limits**: Max 10 requests per minute.
* **Authentication**: None required.

### Digibib (Stadt- und Landesbibliothek)

* **Mechanism**: Metasearch queried via the [lobid.org](https://lobid.org/) API (Linked Open Data) first for stable bibliographical info. Account-level checks are queried via Session-POST requests to `stlb-dortmund.digibib.net`.
* **Rate Limits**: Strictly limited to 1-2 requests per minute.
* **Session Management**: Session cookies should be cached in `.tmp/` to avoid constant re-authentication.

### Scribd

* **Mechanism**: Session-authenticated HTTP requests or Playwright browser automation for doc rendering.
* **Rate Limits**: Max 5 page retrievals per minute.
* **Credentials**: Reads `SCRIBD_USER` and `SCRIBD_PASS`.

### Statista

* **Mechanism**: Authenticated requests using cookies to bypass premium walls.
* **Rate Limits**: Max 3 tables/PDFs per minute.
* **Credentials**: Reads `STATISTA_COOKIE` or session data.

### LinkedIn

* **Mechanism**: Authenticated requests using the `li_at` session cookie.
* **Rate Limits**: Max 2 profile queries per minute to prevent account restriction.
* **Session Management**: Direct login via script is forbidden; always use the `li_at` cookie.
