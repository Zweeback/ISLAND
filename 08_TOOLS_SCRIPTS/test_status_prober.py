import subprocess
import json
from pathlib import Path

def test_no_hardcoded_paths():
    # Run the prober
    subprocess.run(["python", "08_TOOLS_SCRIPTS/status_prober.py"], check=True)

    # Check the output file
    root = Path(__file__).resolve().parents[1]
    status_file = root / "06_GATEWAY_LIVEFEED" / "service_status.jsonl"

    assert status_file.exists(), "Status file was not created"

    with open(status_file, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            # Check source_log
            if data.get("source_log") is not None:
                assert "derzw" not in data["source_log"]
            # Check start_command
            if data.get("start_command") is not None:
                assert "derzw" not in data["start_command"]
