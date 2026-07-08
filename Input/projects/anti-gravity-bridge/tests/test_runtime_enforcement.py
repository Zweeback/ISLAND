import os
import json
import time
import pytest
from fastapi.testclient import TestClient
from orchestrator.main import app
from orchestrator.resource_manager import get_resource_snapshot, admit_job

client = TestClient(app)

def wait_for_job_completion(job_id: str, timeout: float = 2.0) -> dict:
    start_time = time.time()
    while time.time() - start_time < timeout:
        res = client.get(f"/jobs/{job_id}")
        assert res.status_code == 200
        data = res.json()
        if data.get("state") not in ("accepted", "running"):
            return data
        time.sleep(0.05)
    return client.get(f"/jobs/{job_id}").json()

def test_resource_manager_fallback():
    # 1. Test probing with environment overrides
    os.environ["MOCK_VRAM_FREE_MB"] = "8000"
    os.environ["MOCK_RAM_FREE_MB"] = "16000"
    
    snapshot = get_resource_snapshot()
    assert snapshot["vram_free_mb"] == 8000
    assert snapshot["ram_available_mb"] == 16000
    
    # Clean up
    del os.environ["MOCK_VRAM_FREE_MB"]
    del os.environ["MOCK_RAM_FREE_MB"]

def test_simulated_low_vram_rejection():
    # 2. Simulate VRAM too low for meshroom photogrammetry
    os.environ["MOCK_VRAM_FREE_MB"] = "1000"  # 1GB free
    
    admitted, reason = admit_job("meshroom", "meshroom.photogrammetry_reconstruct")
    assert admitted is False
    assert "insufficient_vram" in reason
    
    # Clean up
    del os.environ["MOCK_VRAM_FREE_MB"]

def test_llm_validation_gate_invalid_json():
    # 3. Post a command with malformed LLM raw text
    payload = {
        "schema_version": "bridge.command.v1",
        "command_type": "blender.create_cube",
        "target": "blender",
        "dry_run": True,
        "payload": {
            "llm_raw_text": "MALFORMED_NON_JSON_OUTPUT"
        }
    }
    
    response = client.post("/api/bridge/command", json=payload)
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    
    job_state = wait_for_job_completion(job_id)
    assert job_state["state"] == "failed"
    assert "failed_validation" in job_state["error"]

def test_jit_guard_runtime_change():
    # 4. Simulate a situation where resource availability changes between command accept and execution.
    # Set mock VRAM initially high for routing, then lower it before dispatch
    os.environ["MOCK_VRAM_FREE_MB"] = "1000" # Lock JIT resource manager VRAM check
    
    payload = {
        "schema_version": "bridge.command.v1",
        "command_type": "meshroom.photogrammetry_reconstruct",
        "target": "meshroom",
        "dry_run": False, # Real execution flow to trigger resource manager checks
        "payload": {"images_dir": "test_input"}
    }
    
    response = client.post("/api/bridge/command", json=payload)
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    
    job_state = wait_for_job_completion(job_id)
    assert job_state["state"] == "failed"
    assert "insufficient_vram" in job_state["error"]
    
    del os.environ["MOCK_VRAM_FREE_MB"]

def test_provenance_split():
    # 5. Check if logical and empirical provenance are generated correctly
    payload = {
        "schema_version": "bridge.command.v1",
        "command_type": "unity.sync_assets",
        "target": "unity",
        "dry_run": True,
        "payload": {"project": "island_game"}
    }
    
    response = client.post("/api/bridge/command", json=payload)
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    
    wait_for_job_completion(job_id)
    
    provenance_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "artifacts",
        "jobs",
        job_id,
        "provenance.json"
    )
    assert os.path.exists(provenance_path)
    
    with open(provenance_path, "r", encoding="utf-8") as f:
        prov_data = json.load(f)
        
    assert "logical_provenance" in prov_data
    assert "empirical_provenance" in prov_data
    
    logical = prov_data["logical_provenance"]
    assert "git_commit" in logical
    assert "input_hashes" in logical
    assert logical["command_type"] == "unity.sync_assets"
    
    empirical = prov_data["empirical_provenance"]
    assert "created_at" in empirical
    assert "resource_snapshot" in empirical
    assert "non_determinism_flags" in empirical
