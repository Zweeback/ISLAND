import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone
import os
import re


class ScribdScraper:
    username: str | None
    password: str | None
    cookie: str | None

    def __init__(self, username: str | None = None, password: str | None = None, cookie: str | None = None) -> None:
        self.username = username
        self.password = password
        self.cookie = cookie

    def search(self, query: str) -> dict[str, object]:
        """
        Query Scribd search. Uses session cookie if available, or does a public query.
        """
        params = {"query": query}
        url = "https://www.scribd.com/search?" + urllib.parse.urlencode(params)
        print(f"Searching Scribd: {url}", file=sys.stderr)

        headers: dict[str, str] = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        if self.cookie:
            headers["Cookie"] = self.cookie

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:  # type: ignore
                raw_data = str(response.read().decode('utf-8'))  # type: ignore

            # Find doc links: /document/1234567/title
            links = re.findall(
                r'href="(https://www\.scribd\.com/document/\d+/[^"]+)"', raw_data)
            links = list(set(links))  # remove duplicates

            results: list[dict[str, object]] = []
            for link in links[:10]:
                parts = link.split('/')
                title = parts[-1].replace('-',
                                          ' ') if parts else "Scribd Document"
                results.append({
                    "title": title,
                    "url": link,
                    "id": parts[-2] if len(parts) >= 2 else None
                })

            return {
                "source": "scribd",
                "query": query,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "authenticated": bool(self.cookie),
                "records": results
            }
        except Exception as e:
            return {"error": f"Scribd search failed: {e}"}


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python scraper_scribd.py search <query>", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]
    arg = sys.argv[2]

    username = os.environ.get("SCRIBD_USER")
    password = os.environ.get("SCRIBD_PASS")
    cookie = os.environ.get("SCRIBD_COOKIE")

    scraper = ScribdScraper(username, password, cookie)

    if cmd == "search":
        output = scraper.search(arg)
    else:
        output = {"error": f"Unknown command {cmd}"}

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
