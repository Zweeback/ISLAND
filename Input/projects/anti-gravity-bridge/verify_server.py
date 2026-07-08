import os
import sys
import time
import json
import httpx

URL = "http://127.0.0.1:8420"

def wait_for_server():
    print("Waiting for Anti-Gravity Orchestrator to start on port 8420...")
    for _ in range(15):
        try:
            r = httpx.get(f"{URL}/health", timeout=2.0)
            if r.status_code == 200:
                print("Server is up and operational!")
                return True
        except Exception:
            pass
        time.sleep(0.5)
    print("Server failed to start in time.")
    return False

def test_endpoints():
    print("\n--- Verifying GET /health ---")
    r = httpx.get(f"{URL}/health")
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))

    print("\n--- Verifying GET /capabilities ---")
    r = httpx.get(f"{URL}/capabilities")
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))

    print("\n--- Verifying GET /events (Before Job) ---")
    r = httpx.get(f"{URL}/events")
    print(f"Status: {r.status_code}")
    print(f"Number of events before job: {len(r.json())}")

    print("\n--- Verifying POST /jobs (render dry-run) ---")
    job_payload = {
        "job_type": "render",
        "payload": {
            "action": "render_scene",
            "model_name": "VerificationSphere",
            "engine": "CYCLES"
        }
    }
    r = httpx.post(f"{URL}/jobs", json=job_payload)
    print(f"Status: {r.status_code}")
    job_data = r.json()
    print(json.dumps(job_data, indent=2))
    job_id = job_data["job_id"]

    print("\nSleeping 3 seconds for background job execution...")
    time.sleep(3.0)

    print(f"\n--- Verifying GET /jobs/{job_id} ---")
    r = httpx.get(f"{URL}/jobs/{job_id}")
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))

    print("\n--- Verifying GET /events (After Job) ---")
    r = httpx.get(f"{URL}/events")
    print(f"Status: {r.status_code}")
    events = r.json()
    print(f"Number of events after job: {len(events)}")
    print("Last 5 events:")
    for ev in events[-5:]:
        print(f"  - Event: {ev['event']} at {ev['timestamp']}")

    print("\n--- Verifying state and provenance files on disk ---")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    job_dir = os.path.join(base_dir, "artifacts", "jobs", job_id)

    state_file = os.path.join(job_dir, "job_state.json")
    prov_file = os.path.join(job_dir, "provenance.json")

    print(f"Job state file exists: {os.path.exists(state_file)}")
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            print("job_state.json content:")
            print(json.dumps(json.load(f), indent=2))

    print(f"Provenance file exists: {os.path.exists(prov_file)}")
    if os.path.exists(prov_file):
        with open(prov_file, "r") as f:
            print("provenance.json content:")
            print(json.dumps(json.load(f), indent=2))

if __name__ == "__main__":
    if wait_for_server():
        test_endpoints()
