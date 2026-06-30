from __future__ import annotations
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone
import os
import re


class StatistaScraper:
    username: str | None
    password: str | None
    cookie: str | None

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        cookie: str | None = None,
    ) -> None:
        self.username = username
        self.password = password
        self.cookie = cookie

    def search(self, query: str) -> dict[str, object]:
        """
        Search Statista. Uses premium cookie if configured.
        """
        params = {"q": query}
        url = "https://de.statista.com/suche/?" + urllib.parse.urlencode(params)
        print(f"Searching Statista: {url}", file=sys.stderr)

        headers: dict[str, str] = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        if self.cookie:
            headers["Cookie"] = self.cookie

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:  # type: ignore
                raw_bytes: bytes = response.read()  # type: ignore
                raw_data: str = raw_bytes.decode("utf-8")

            # Extract statistics links: e.g., /statistik/daten/studie/12345/umfrage/...
            links: list[str] = re.findall(
                r'href="(/statistik/daten/studie/\d+/[^"]+)"', raw_data
            )
            links = list(set(links))  # remove duplicates

            results: list[dict[str, object]] = []
            for link in links[:10]:
                full_link = f"https://de.statista.com{link}"
                parts = link.split("/")
                title = parts[-1].replace("-", " ") if parts else "Statista Report"
                results.append(
                    {
                        "title": title,
                        "url": full_link,
                        "id": parts[4] if len(parts) >= 5 else None,
                    }
                )

            return {
                "source": "statista",
                "query": query,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "authenticated": bool(self.cookie),
                "records": results,
            }
        except Exception as e:
            return {"error": f"Statista search failed: {e}"}


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python scraper_statista.py search <query>", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]
    arg = sys.argv[2]

    username = os.environ.get("STATISTA_USER")
    password = os.environ.get("STATISTA_PASS")
    cookie = os.environ.get("STATISTA_COOKIE")

    scraper = StatistaScraper(username, password, cookie)

    if cmd == "search":
        output = scraper.search(arg)
    else:
        output = {"error": f"Unknown command {cmd}"}

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
