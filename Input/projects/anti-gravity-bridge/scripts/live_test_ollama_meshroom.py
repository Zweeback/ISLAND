"""
Live integration test: real nvidia-smi + running Ollama + Meshroom job dispatch.
No MOCK_VRAM_FREE_MB — uses actual GPU telemetry.
"""
import json
import os
import subprocess
import sys
import time

import httpx

BRIDGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8423


def nvidia_smi_snapshot() -> str:
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.used,memory.free,memory.total", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        return r.stdout.strip()
    except Exception as e:
        return f"nvidia-smi unavailable: {e}"


def ollama_ps() -> dict:
    try:
        r = httpx.get("http://127.0.0.1:11434/api/ps", timeout=3.0)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def run_live_test() -> bool:
    print("=== LIVE TEST: Ollama + Meshroom (real nvidia-smi) ===\n")
    print(f"GPU: {nvidia_smi_snapshot()}")
    print(f"Ollama PS: {json.dumps(ollama_ps(), indent=2)}\n")

    env = os.environ.copy()
    env.pop("MOCK_VRAM_FREE_MB", None)
    env.pop("MOCK_RAM_FREE_MB", None)
    env.pop("MOCK_OLLAMA_UNLOAD", None)
    env["MESHROOM_DRY_RUN"] = "true"

    server = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "orchestrator.main:app",
            "--host", "127.0.0.1",
            f"--port", str(PORT),
        ],
        cwd=BRIDGE_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    url = f"http://127.0.0.1:{PORT}"
    try:
        connected = False
        for _ in range(30):
            try:
                if httpx.get(f"{url}/health", timeout=1.0).status_code == 200:
                    connected = True
                    break
            except Exception:
                pass
            time.sleep(0.3)
        if not connected:
            print("FAIL: server did not start")
            return False

        print("Bridge server up on port", PORT)

        payload = {
            "schema_version": "bridge.command.v1",
            "command_type": "meshroom.photogrammetry_reconstruct",
            "target": "meshroom",
            "dry_run": False,
            "payload": {"images_dir": "live_test_photos", "project_id": "live_01"},
        }
        resp = httpx.post(f"{url}/api/bridge/command", json=payload, timeout=5.0)
        print(f"POST /api/bridge/command -> {resp.status_code}")
        data = resp.json()
        job_id = data["job_id"]
        print(f"job_id: {job_id}")

        state = None
        error = None
        for _ in range(30):
            job = httpx.get(f"{url}/jobs/{job_id}", timeout=2.0).json()
            state = job.get("state")
            error = job.get("error")
            if state not in ("accepted", "validating", "admission_check", "running"):
                break
            time.sleep(0.2)

        history = httpx.get(f"{url}/jobs/{job_id}", timeout=2.0).json().get("history", [])
        history_states = [h["state"] for h in history]

        events = httpx.get(f"{url}/events", timeout=3.0).json()
        job_events = [
            e for e in events
            if (e.get("data") or {}).get("job_id") == job_id
            or e.get("job_id") == job_id
        ]
        event_types = [e.get("type") or e.get("event") for e in job_events]

        deferred_path = os.path.join(BRIDGE_DIR, "artifacts", "deferred", f"{job_id}.json")
        deferred_exists = os.path.isfile(deferred_path)

        print(f"\nFinal state: {state}")
        print(f"Error: {error}")
        print(f"History: {history_states}")
        print(f"Event types: {event_types}")
        print(f"Deferred artifact persisted: {deferred_exists}")
        print(f"GPU after dispatch: {nvidia_smi_snapshot()}")

        ok = (
            resp.status_code == 202
            and state == "deferred"
            and "insufficient_vram" in (error or "")
            and "running" not in history_states
            and "job.started" not in event_types
            and any(t == "job.deferred" for t in event_types)
            and deferred_exists
        )
        print(f"\nLIVE TEST {'PASSED' if ok else 'FAILED'}")
        return ok
    finally:
        server.terminate()
        server.wait(timeout=10)


if __name__ == "__main__":
    sys.exit(0 if run_live_test() else 1)