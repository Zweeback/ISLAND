"""
Concurrent stress test: Blender + Meshroom jobs under simulated Ollama VRAM pressure.
Verifies JIT guards reject all jobs without spawning subprocesses when VRAM is exhausted.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

BRIDGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = int(os.getenv("STRESS_TEST_PORT", "8423"))
BASE_URL = f"http://127.0.0.1:{PORT}"


def _wait_for_server(timeout: float = 8.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if httpx.get(f"{BASE_URL}/health", timeout=1.0).status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.2)
    return False


def _dispatch_job(client: httpx.Client, label: str, payload: dict) -> dict:
    response = client.post(f"{BASE_URL}/api/bridge/command", json=payload, timeout=10.0)
    response.raise_for_status()
    job_id = response.json()["job_id"]

    state = None
    error = None
    history: list = []
    for _ in range(60):
        job = client.get(f"{BASE_URL}/jobs/{job_id}", timeout=5.0).json()
        state = job.get("state")
        error = job.get("error")
        history = job.get("history", [])
        terminal = state not in ("accepted", "running", "validating", "ready", "retrying")
        if terminal or (state in ("deferred", "failed") and error):
            break
        time.sleep(0.15)

    return {
        "label": label,
        "job_id": job_id,
        "state": state,
        "error": error,
        "history_states": [h.get("state") for h in history],
    }


def run_stress_test() -> bool:
    print("Starting concurrent stress test (simulated Ollama VRAM pressure)...")
    env = os.environ.copy()
    env["MOCK_VRAM_FREE_MB"] = "2000"
    env["MOCK_RAM_FREE_MB"] = "16000"
    env["MOCK_OLLAMA_UNLOAD"] = "false"

    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "orchestrator.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(PORT),
        ],
        cwd=BRIDGE_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    report: dict = {
        "mock_vram_free_mb": 2000,
        "mock_ollama_unload": False,
        "jobs": [],
        "success": False,
    }

    try:
        if not _wait_for_server():
            print("ERROR: Server failed to start")
            return False

        jobs = [
            (
                "blender_render_1",
                {
                    "schema_version": "bridge.command.v1",
                    "command_type": "blender.render_scene",
                    "target": "blender",
                    "dry_run": False,
                    "payload": {"model_name": "ConcurrentA"},
                },
            ),
            (
                "blender_render_2",
                {
                    "schema_version": "bridge.command.v1",
                    "command_type": "blender.render_scene",
                    "target": "blender",
                    "dry_run": False,
                    "payload": {"model_name": "ConcurrentB"},
                },
            ),
            (
                "meshroom_reconstruct",
                {
                    "schema_version": "bridge.command.v1",
                    "command_type": "meshroom.photogrammetry_reconstruct",
                    "target": "meshroom",
                    "dry_run": False,
                    "payload": {"images_dir": "stress_input"},
                },
            ),
        ]

        with httpx.Client() as client:
            with ThreadPoolExecutor(max_workers=3) as pool:
                futures = [
                    pool.submit(_dispatch_job, client, label, payload)
                    for label, payload in jobs
                ]
                for future in as_completed(futures):
                    result = future.result()
                    report["jobs"].append(result)
                    print(
                        f"  {result['label']}: {result['state']} "
                        f"(history={result['history_states']})"
                    )

        all_rejected = all(
            j["state"] == "deferred" and j["error"] and "insufficient_vram" in j["error"]
            for j in report["jobs"]
        )
        no_running_leak = all("running" not in j["history_states"] for j in report["jobs"])

        report["success"] = all_rejected and no_running_leak
        print(json.dumps(report, indent=2))

        if report["success"]:
            print("\nCONCURRENT STRESS TEST SUCCESSFUL")
        else:
            print("\nCONCURRENT STRESS TEST FAILED")
        return report["success"]
    finally:
        server.terminate()
        server.wait(timeout=5)


if __name__ == "__main__":
    sys.exit(0 if run_stress_test() else 1)