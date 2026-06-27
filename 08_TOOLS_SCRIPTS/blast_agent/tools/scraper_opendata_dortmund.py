from __future__ import annotations
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Optional

BASE_URL = "https://open-data.dortmund.de/api/explore/v2.1"

def query_opendata(endpoint: str, params: Optional[dict[str, Any]] = None) -> Any:
    url = f"{BASE_URL}/{endpoint}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    
    print(f"Querying URL: {url}", file=sys.stderr)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ZentraleInselAgent/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"API Request Failed: {e}", file=sys.stderr)
        return {"error": str(e)}

def search_datasets(query: str) -> dict[str, Any]:
    params = {
        "q": query,
        "limit": 10
    }
    res = query_opendata("catalog/datasets", params)
    if not isinstance(res, dict) or "error" in res:
        # Cast/wrap error response safely
        err_msg = res.get("error", "Unknown error") if isinstance(res, dict) else str(res)
        return {"error": err_msg}
    
    results = []
    datasets_list = res.get("results", [])
    if isinstance(datasets_list, list):
        for ds in datasets_list:
            if isinstance(ds, dict):
                metas = ds.get("metas", {})
                default_meta = metas.get("default", {}) if isinstance(metas, dict) else {}
                
                results.append({
                    "dataset_id": ds.get("dataset_id"),
                    "title": default_meta.get("title") if isinstance(default_meta, dict) else None,
                    "description": default_meta.get("description") if isinstance(default_meta, dict) else None,
                    "records_count": default_meta.get("records_count") if isinstance(default_meta, dict) else None
                })
                
    return {
        "source": "opendata_dortmund",
        "query": query,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": results
    }

def get_records(dataset_id: str, limit: int = 10) -> dict[str, Any]:
    params = {
        "limit": limit
    }
    res = query_opendata(f"catalog/datasets/{dataset_id}/records", params)
    if not isinstance(res, dict) or "error" in res:
        err_msg = res.get("error", "Unknown error") if isinstance(res, dict) else str(res)
        return {"error": err_msg}
    
    records = []
    results_list = res.get("results", [])
    if isinstance(results_list, list):
        for rec in results_list:
            if isinstance(rec, dict):
                records.append({
                    "id": rec.get("id"),
                    "timestamp": rec.get("timestamp"),
                    "fields": rec.get("fields", {})
                })
                
    return {
        "source": f"opendata_dortmund_{dataset_id}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "records": records
    }

def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python scraper_opendata_dortmund.py <search_datasets|get_records> <query|dataset_id>", file=sys.stderr)
        sys.exit(1)
    
    cmd = sys.argv[1]
    arg = sys.argv[2]
    
    if cmd == "search_datasets":
        output = search_datasets(arg)
    elif cmd == "get_records":
        output = get_records(arg)
    else:
        output = {"error": f"Unknown command {cmd}"}
        
    print(json.dumps(output, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
