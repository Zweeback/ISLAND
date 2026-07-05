#!/usr/bin/env python3
"""
GAMEDEV BASE MULTI LLM LIVEFEED ORCHESTRATOR
Orchestrates the progress and all subprojects across the Zentrale Insel Workspace.
"""

import json
from pathlib import Path
import subprocess
import sys
import time


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> None:
    workspace_root = Path(__file__).resolve().parent.parent
    repos_manifest = workspace_root / "03_MANIFESTE_INVENTAR" / "repos_merged.jsonl"
    status_file = workspace_root / "06_GATEWAY_LIVEFEED" / "service_status.jsonl"
    agent_loop_script = (
        workspace_root / "08_TOOLS_SCRIPTS" / "blast_agent" / "tools" / "agent_loop.py"
    )

    print("=== GAMEDEV BASE MULTI LLM LIVEFEED ORCHESTRATOR ===")
    print("Merging progress across all subprojects...\n")

    repos = load_jsonl(repos_manifest)
    print(f"Loaded {len(repos)} registered subprojects.")

    services = load_jsonl(status_file)
    print(f"Tracking {len(services)} live services.\n")

    print("Initiating Multi-LLM Autonomous Loop...")
    if agent_loop_script.exists():
        try:
            res = subprocess.run(
                [sys.executable, str(agent_loop_script)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            print("Agent Output:")
            print(res.stdout)
        except subprocess.TimeoutExpired:
            print("Agent loop timed out.")
    else:
        print("Agent loop not found.")

    print("\nOrchestration cycle complete.")


if __name__ == "__main__":
    main()
