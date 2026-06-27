import sys
from pathlib import Path
import json

# Add the directory containing tools to sys.path so we can import AgentLoop
workspace_root = Path("08_TOOLS_SCRIPTS/blast_agent").resolve()
sys.path.append(str(workspace_root / "tools"))

from agent_loop import AgentLoop  # noqa: E402  # noqa: E402


def test_execute_tool_validation():
    print("Testing tool_name validation in agent_loop.py")
    loop = AgentLoop(workspace_root)

    # Test valid tool name (scraper_digibib.py exists in tools/)
    valid_tool_name = "scraper_digibib"
    print(f"Testing valid tool name: {valid_tool_name}")
    # We pass an invalid argument like --help to avoid actually running a full scrape
    result = loop.execute_tool(valid_tool_name, ["--help"])
    try:
        res_json = json.loads(result)
        if "error" in res_json and "Invalid tool name" in res_json["error"]:
            print("❌ Valid tool name was incorrectly rejected.")
            sys.exit(1)
        else:
            print("✅ Valid tool name passed validation.")
    except json.JSONDecodeError:
        # If it doesn't return JSON, it probably ran the script and returned stdout
        print("✅ Valid tool name passed validation (returned non-JSON output).")

    # Test invalid tool name (path traversal attempt)
    invalid_tool_name = "../agent_loop"
    print(f"Testing invalid tool name: {invalid_tool_name}")
    result = loop.execute_tool(invalid_tool_name, [])
    try:
        res_json = json.loads(result)
        if "error" in res_json and "Invalid tool name" in res_json["error"]:
            print("✅ Invalid tool name was correctly rejected.")
        else:
            print(f"❌ Invalid tool name was not rejected correctly. Got: {result}")
            sys.exit(1)
    except json.JSONDecodeError:
        print(
            f"❌ Invalid tool name was not rejected correctly (returned non-JSON). Got: {result}"
        )
        sys.exit(1)


if __name__ == "__main__":
    test_execute_tool_validation()
