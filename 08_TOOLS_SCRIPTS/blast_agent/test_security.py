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

    # Test parameter injection in execute_tool arguments
    res_param_inject = loop.execute_tool("scraper_opendata_dortmund", ["--help"])
    parsed_param_inject = json.loads(res_param_inject)
    assert "error" in parsed_param_inject, "Expected an error for parameter injection."
    assert "Security Violation: Parameter injection detected" in parsed_param_inject["error"], "Expected parameter injection error."

    # Test bypass parameter injection in execute_tool arguments
    res_bypass_inject = loop.execute_tool("scraper_opendata_dortmund", [" --malicious"])
    parsed_bypass_inject = json.loads(res_bypass_inject)
    assert "error" in parsed_bypass_inject, "Expected an error for bypass parameter injection."
    assert "Security Violation: Parameter injection detected" in parsed_bypass_inject["error"], "Expected bypass parameter injection error."

    # Test command injection in execute_tool arguments
    res_cmd_inject = loop.execute_tool("scraper_opendata_dortmund", ["search", "Bibliotheken; rm -rf /"])
    parsed_cmd_inject = json.loads(res_cmd_inject)
    assert "error" in parsed_cmd_inject, "Expected an error for command injection."
    assert "Security Violation: Shell metacharacter detected" in parsed_cmd_inject["error"], "Expected command injection error."

    print("All security tests passed.")


if __name__ == "__main__":
    test_security()
