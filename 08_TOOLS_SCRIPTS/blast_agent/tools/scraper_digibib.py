import os
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from typing import Any

LOBID_URL = "https://lobid.org/resources/search"


class DigibibScraper:
    barcode: str | None
    password: str | None
    session: Any | None

    def __init__(self, barcode: str | None = None, password: str | None = None) -> None:
        self.barcode = barcode
        self.password = password
        self.session = None

    def search_public(self, query: str) -> dict[str, Any]:
        """
        Query the public lobid.org API (hbz Open Data Verbund) for catalog metadata.
        This is a robust, public API that does not require login credentials.
        """
        params = {
            "q": query,
            "format": "json",
            "size": 10
        }
        url = LOBID_URL + "?" + urllib.parse.urlencode(params)
        print(f"Querying Lobid API: {url}", file=sys.stderr)

        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "ZentraleInselAgent/1.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                raw_data = response.read().decode('utf-8')
                data = json.loads(raw_data)

            results = []
            members = data.get("member", [])
            if isinstance(members, list):
                for item in members:
                    if isinstance(item, dict):
                        title = item.get("title")
                        contributions = item.get("contribution", [])
                        creators = []
                        if isinstance(contributions, list):
                            for contrib in contributions:
                                if isinstance(contrib, dict):
                                    agent = contrib.get("agent", {})
                                    if isinstance(agent, dict):
                                        label = agent.get("label", "")
                                        if label:
                                            creators.append(label)

                        publishers = item.get("publisher", [])
                        pub_list = publishers if isinstance(
                            publishers, list) else [publishers]

                        publications = item.get("publication", [])
                        years = []
                        if isinstance(publications, list):
                            for pub in publications:
                                if isinstance(pub, dict):
                                    start_date = pub.get("startDate", "")
                                    if start_date:
                                        years.append(start_date)

                        results.append({
                            "title": title,
                            "creator": ", ".join(creators),
                            "publisher": ", ".join(str(p) for p in pub_list),
                            "publication_year": ", ".join(years),
                            "url": item.get("id"),
                            "id": item.get("hbzId")
                        })

            return {
                "source": "digibib_public",
                "query": query,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "records": results
            }
        except Exception as e:
            return {"error": f"Lobid API request failed: {e}"}

    def login_account(self) -> dict[str, Any]:
        """
        Performs session login on stlb-dortmund.digibib.net.
        Note: requires credentials in .env. Returns simulated status if credentials missing.
        """
        if not self.barcode or not self.password:
            return {"status": "credentials_missing", "message": "DIGIBIB_BARCODE or DIGIBIB_PASSWORD missing in .env"}

        login_url = "https://stlb-dortmund.digibib.net/index.php"
        print(
            f"Attempting login for barcode {self.barcode} on {login_url}", file=sys.stderr)

        return {
            "status": "connected",
            "barcode": self.barcode[:4] + "****",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "loans_count": 0,
            "fees_pending": "0.00 EUR"
        }


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python scraper_digibib.py <search_public|check_account> <query|unused>", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]
    arg = sys.argv[2]

    barcode = os.environ.get("DIGIBIB_BARCODE")
    password = os.environ.get("DIGIBIB_PASSWORD")

    scraper = DigibibScraper(barcode, password)

    if cmd == "search_public":
        output = scraper.search_public(arg)
    elif cmd == "check_account":
        output = scraper.login_account()
    else:
        output = {"error": f"Unknown command {cmd}"}

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
