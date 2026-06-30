from __future__ import annotations
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone
import os
import re


class LinkedInScraper:
    li_at: str | None

    def __init__(self, li_at_cookie: str | None = None) -> None:
        self.li_at = li_at_cookie

    def search_jobs(self, query: str) -> dict[str, object]:
        """
        Search for LinkedIn jobs or profiles. Requires li_at cookie to fetch real data.
        """
        headers: dict[str, str] = {}
        if not self.li_at:
            url = "https://www.linkedin.com/jobs/search/?" + urllib.parse.urlencode(
                {"keywords": query}
            )
            print(f"Querying LinkedIn public jobs: {url}", file=sys.stderr)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        else:
            url = (
                "https://www.linkedin.com/voyager/api/search/hits?"
                + urllib.parse.urlencode(
                    {"q": "all", "keywords": query, "origin": "GLOBAL_SEARCH_HEADER"}
                )
            )
            print(f"Querying authenticated LinkedIn API: {url}", file=sys.stderr)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Cookie": f"li_at={self.li_at}",
                "Csrf-Token": "ajax:999999",
                "X-RestLi-Protocol-Version": "2.0.0",
            }

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:  # type: ignore
                content = str(response.read().decode("utf-8"))  # type: ignore

            records: list[dict[str, object]] = []
            if self.li_at:
                data: dict[str, object] = json.loads(content)  # type: ignore
                elements_list = data.get("elements", [])  # type: ignore
                if isinstance(elements_list, list):
                    for hit in elements_list:
                        if isinstance(hit, dict):  # type: ignore
                            title_text = hit.get("title", {})  # type: ignore
                            title = title_text.get("text", "LinkedIn Entity") if isinstance(title_text, dict) else "LinkedIn Entity"  # type: ignore

                            subline_text = hit.get("subline", {})  # type: ignore
                            snippet = subline_text.get("text") if isinstance(subline_text, dict) else None  # type: ignore

                            records.append(
                                {
                                    "title": title,
                                    "url": hit.get("navigationUrl"),  # type: ignore
                                    "snippet": snippet,
                                }
                            )
            else:
                job_ids: list[str] = re.findall(r"/jobs/view/(\d+)", content)
                job_ids = list(set(job_ids))
                for jid in job_ids[:10]:
                    records.append(
                        {
                            "title": f"LinkedIn Job Listing ({jid})",
                            "url": f"https://www.linkedin.com/jobs/view/{jid}/",
                            "snippet": "Public job listing retrieved without authentication.",
                        }
                    )

            return {
                "source": "linkedin",
                "query": query,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "authenticated": bool(self.li_at),
                "records": records,
            }
        except Exception as e:
            return {"error": f"LinkedIn request failed: {e}"}


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python scraper_linkedin.py search <query>", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]
    arg = sys.argv[2]

    li_at = os.environ.get("LINKEDIN_COOKIE_LI_AT")

    scraper = LinkedInScraper(li_at)

    if cmd == "search":
        output = scraper.search_jobs(arg)
    else:
        output = {"error": f"Unknown command {cmd}"}

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
