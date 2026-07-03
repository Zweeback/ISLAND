import sys
import subprocess
from pathlib import Path


def test_security():
    blast_agent_path = Path(__file__).parent / "blast_agent.py"

    # Test valid scraper
    res_valid = subprocess.run(
        [
            sys.executable,
            str(blast_agent_path),
            "scrape",
            "opendata_dortmund",
            "search",
        ],
        capture_output=True,
        text=True,
    )
    assert (
        "Usage: python scraper_opendata_dortmund.py" in res_valid.stdout
        or "Usage: python scraper_opendata_dortmund.py" in res_valid.stderr
        or res_valid.returncode == 0
    ), "Valid scraper execution failed."

    # Test path traversal in blast_agent.py
    res_invalid = subprocess.run(
        [sys.executable, str(blast_agent_path), "scrape", "../../../etc/passwd"],
        capture_output=True,
        text=True,
    )
    assert res_invalid.returncode != 0, "Invalid scraper execution should have failed."
    assert (
        "Error: Invalid scraper name" in res_invalid.stderr
    ), "Error message not found in stderr."

    # Test execute_tool in AgentLoop
    agent_loop_path = Path(__file__).parent
    sys.path.append(str(agent_loop_path))
    from tools.agent_loop import AgentLoop

    loop = AgentLoop(agent_loop_path)
    res_tool = loop.execute_tool("../../../etc/passwd", [])
    import json

    parsed = json.loads(res_tool)
    assert "error" in parsed, "Expected an error."
    assert "Invalid tool name" in parsed["error"], "Expected invalid tool name error."

    print("All security tests passed.")


if __name__ == "__main__":
    test_security()

def test_opendata_scraper_ssrf():
    blast_agent_path = Path(__file__).parent / "blast_agent.py"
    res = subprocess.run(
        [
            sys.executable,
            str(blast_agent_path),
            "scrape",
            "opendata_dortmund",
            "get_records",
            "../../foo"
        ],
        capture_output=True,
        text=True,
    )
    # The vulnerability was that ../../foo would traverse the path.
    # With urllib.parse.quote, it becomes ..%2F..%2Ffoo, which is safe.
    # The API will just return a 404/Not Found for that dataset_id instead of traversing.
    # Or at least, the scraper will handle it safely and likely output an error about the dataset not found,
    # instead of successfully making a query to an unintended endpoint.

    # Actually, we can check if the encoded URL is in the output because `query_opendata` prints the URL.
    assert "..%2F..%2Ffoo" in res.stderr or "..%2F..%2Ffoo" in res.stdout, "Dataset ID was not properly encoded."
    assert "catalog/datasets/../../foo" not in res.stderr and "catalog/datasets/../../foo" not in res.stdout, "Unencoded dataset ID was used!"
