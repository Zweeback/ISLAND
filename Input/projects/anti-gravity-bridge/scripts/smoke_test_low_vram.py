import os
import sys
import time
import subprocess
import httpx
import json

def run_smoke_test():
    print("Starting server for Smoke Test...")
    env = os.environ.copy()
    env["MOCK_VRAM_FREE_MB"] = "1000"
    
    server_process = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", 
            "orchestrator.main:app", 
            "--host", "127.0.0.1", 
            "--port", "8422"
        ],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    url = "http://127.0.0.1:8422"
    
    # Wait for server to start
    print("Waiting for server to respond on port 8422...")
    connected = False
    for _ in range(20):
        try:
            r = httpx.get(f"{url}/health", timeout=1.0)
            if r.status_code == 200:
                connected = True
                break
        except Exception:
            pass
        time.sleep(0.2)
        
    if not connected:
        print("Error: Server failed to start.")
        server_process.terminate()
        return False

    print("Server is up! Dispatching Meshroom job with dry_run=False under low VRAM simulation...")
    
    payload = {
        "schema_version": "bridge.command.v1",
        "command_type": "meshroom.photogrammetry_reconstruct",
        "target": "meshroom",
        "dry_run": False,
        "payload": {
            "images_dir": "my_photos"
        }
    }
    
    try:
        response = httpx.post(f"{url}/api/bridge/command", json=payload, timeout=5.0)
        assert response.status_code == 202
        data = response.json()
        job_id = data["job_id"]
        print(f"Job successfully queued with ID: {job_id}")
        
        # Poll state
        print("Polling job state...")
        state = None
        error = None
        for _ in range(20):
            r = httpx.get(f"{url}/jobs/{job_id}", timeout=2.0)
            job_state = r.json()
            state = job_state.get("state")
            error = job_state.get("error")
            if state not in ("accepted", "running"):
                break
            time.sleep(0.1)
            
        print(f"Final Job State: {state}")
        print(f"Final Job Error: {error}")
        
        # Assertions
        assert state == "deferred"
        assert "insufficient_vram" in error

        r = httpx.get(f"{url}/jobs/{job_id}", timeout=2.0)
        history_states = [h["state"] for h in r.json().get("history", [])]
        assert "running" not in history_states
        print(f"State machine history (no running leak): {history_states}")

        # Check event logging
        print("Verifying events...")
        r = httpx.get(f"{url}/events")
        events = r.json()
        def _event_type(e):
            return e.get("type") or e.get("event")

        def _event_job_id(e):
            data = e.get("data") if isinstance(e.get("data"), dict) else e
            return data.get("job_id")

        started_events = [
            e for e in events
            if _event_type(e) == "job.started" and _event_job_id(e) == job_id
        ]
        assert len(started_events) == 0, "Rejected job must not emit job.started"

        deferred_events = [
            e for e in events
            if _event_type(e) == "job.deferred" and _event_job_id(e) == job_id
        ]
        assert len(deferred_events) > 0
        print("Deferred event verified:")
        print(json.dumps(deferred_events[-1], indent=2))
        print("job.started correctly absent for rejected job")
        
        print("\nSMOKE TEST SUCCESSFUL!")
        success = True
    except Exception as e:
        print(f"\nSMOKE TEST FAILED: {e}")
        success = False
    finally:
        server_process.terminate()
        server_process.wait()
        print("Server process shut down.")
        
    return success

if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)
