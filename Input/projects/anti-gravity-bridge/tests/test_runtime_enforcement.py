import os
import json
import time
import asyncio
from unittest.mock import patch, AsyncMock
import pytest
from fastapi.testclient import TestClient
from orchestrator.main import app
from orchestrator.resource_manager import (
    get_resource_snapshot,
    admit_job,
    admit_job_with_recovery,
)

client = TestClient(app)

MOCK_ENV_KEYS = (
    "MOCK_VRAM_FREE_MB",
    "MOCK_RAM_FREE_MB",
    "MOCK_OLLAMA_UNLOAD",
    "MOCK_VRAM_FREED_MB",
    "MESHROOM_DRY_RUN",
    "ALLOW_OLLAMA_UNLOAD",
)


def _job_events(job_id: str, limit: int = 50) -> list:
    return client.get(f"/events?limit={limit}").json()


def _event_matches(job_event: dict, event_type: str, target_job_id: str) -> bool:
    event_kind = job_event.get("type") or job_event.get("event")
    if event_kind != event_type:
        return False
    payload = job_event.get("data") if isinstance(job_event.get("data"), dict) else job_event
    return payload.get("job_id") == target_job_id


@pytest.fixture(autouse=True)
def clean_resource_mock_env():
    for key in MOCK_ENV_KEYS:
        os.environ.pop(key, None)
    yield
    for key in MOCK_ENV_KEYS:
        os.environ.pop(key, None)


def wait_for_job_completion(job_id: str, timeout: float = 2.0) -> dict:
    start_time = time.time()
    while time.time() - start_time < timeout:
        res = client.get(f"/jobs/{job_id}")
        assert res.status_code == 200
        data = res.json()
        if data.get("state") not in ("accepted", "running", "retrying"):
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
    os.environ["MOCK_VRAM_FREE_MB"] = "1000"

    payload = {
        "schema_version": "bridge.command.v1",
        "command_type": "meshroom.photogrammetry_reconstruct",
        "target": "meshroom",
        "dry_run": False,
        "payload": {"images_dir": "test_input"},
    }

    response = client.post("/api/bridge/command", json=payload)
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    job_state = wait_for_job_completion(job_id)
    assert job_state["state"] == "deferred"
    assert "insufficient_vram" in job_state["error"]

    history_states = [h["state"] for h in job_state.get("history", [])]
    assert "running" not in history_states

    events = _job_events(job_id)
    assert not any(_event_matches(e, "job.started", job_id) for e in events)
    assert any(_event_matches(e, "job.deferred", job_id) for e in events)
    assert not any(_event_matches(e, "job.failed", job_id) for e in events)

    del os.environ["MOCK_VRAM_FREE_MB"]


def test_ollama_unload_vram_recovery_unit():
    os.environ["MOCK_VRAM_FREE_MB"] = "3000"
    os.environ["MOCK_RAM_FREE_MB"] = "16000"
    os.environ["ALLOW_OLLAMA_UNLOAD"] = "true"
    os.environ["MOCK_OLLAMA_UNLOAD"] = "true"
    os.environ["MOCK_VRAM_FREED_MB"] = "4000"

    admitted, reason, unloaded = asyncio.run(
        admit_job_with_recovery("meshroom", "meshroom.photogrammetry_reconstruct")
    )
    assert unloaded is True
    assert admitted is True
    assert reason == "resources_available"
    assert get_resource_snapshot()["vram_free_mb"] == 7000

    for key in (
        "MOCK_VRAM_FREE_MB",
        "MOCK_RAM_FREE_MB",
        "ALLOW_OLLAMA_UNLOAD",
        "MOCK_OLLAMA_UNLOAD",
        "MOCK_VRAM_FREED_MB",
    ):
        del os.environ[key]


@patch("orchestrator.resource_manager.unload_ollama_model")
def test_ollama_unload_requires_allow_flag(mock_unload):
    os.environ["MOCK_VRAM_FREE_MB"] = "3000"
    os.environ["MOCK_RAM_FREE_MB"] = "16000"

    admitted, reason, unloaded = asyncio.run(
        admit_job_with_recovery("meshroom", "meshroom.photogrammetry_reconstruct")
    )
    assert admitted is False
    assert "insufficient_vram" in reason
    assert unloaded is False
    mock_unload.assert_not_called()


@patch("orchestrator.resource_manager.unload_ollama_model", new_callable=AsyncMock)
def test_ollama_unload_single_recovery_attempt(mock_unload):
    mock_unload.return_value = False
    os.environ["MOCK_VRAM_FREE_MB"] = "3000"
    os.environ["MOCK_RAM_FREE_MB"] = "16000"
    os.environ["ALLOW_OLLAMA_UNLOAD"] = "true"

    async def _run():
        return await admit_job_with_recovery(
            "meshroom", "meshroom.photogrammetry_reconstruct"
        )

    admitted, reason, unloaded = asyncio.run(_run())
    assert admitted is False
    assert unloaded is False
    mock_unload.assert_called_once()


@patch("orchestrator.main.run_meshroom_pipeline")
def test_ollama_unload_recovery_integration(mock_meshroom):
    mock_meshroom.return_value = {
        "success": True,
        "artifacts": ["artifacts/jobs/meshroom_reconstruction_test.obj"],
    }
    os.environ["MOCK_VRAM_FREE_MB"] = "3000"
    os.environ["MOCK_RAM_FREE_MB"] = "16000"
    os.environ["ALLOW_OLLAMA_UNLOAD"] = "true"
    os.environ["MOCK_OLLAMA_UNLOAD"] = "true"
    os.environ["MOCK_VRAM_FREED_MB"] = "4000"

    payload = {
        "schema_version": "bridge.command.v1",
        "command_type": "meshroom.photogrammetry_reconstruct",
        "target": "meshroom",
        "dry_run": False,
        "payload": {"images_dir": "test_input"},
    }

    response = client.post("/api/bridge/command", json=payload)
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    job_state = wait_for_job_completion(job_id, timeout=3.0)
    assert job_state["state"] in ("completed", "succeeded")
    history_states = [h["state"] for h in job_state.get("history", [])]
    assert "running" in history_states
    assert "succeeded" in history_states or job_state["state"] == "completed"

    events = _job_events(job_id)
    assert any(_event_matches(e, "job.started", job_id) for e in events)
    ollama_events = [
        e for e in events if _event_matches(e, "job.ollama_unloaded", job_id)
    ]
    assert len(ollama_events) >= 1
    mock_meshroom.assert_called_once()


def test_state_machine_no_running_on_guard_rejection():
    os.environ["MOCK_VRAM_FREE_MB"] = "1000"
    os.environ["MOCK_RAM_FREE_MB"] = "16000"

    payload = {
        "schema_version": "bridge.command.v1",
        "command_type": "blender.render_scene",
        "target": "blender",
        "dry_run": False,
        "payload": {"model_name": "StressSphere"},
    }

    response = client.post("/api/bridge/command", json=payload)
    job_id = response.json()["job_id"]
    job_state = wait_for_job_completion(job_id)

    assert job_state["state"] == "deferred"
    history_states = [h["state"] for h in job_state.get("history", [])]
    assert "running" not in history_states
    assert "deferred" in history_states
    assert history_states[-1] == "deferred"

    events = _job_events(job_id)
    assert not any(_event_matches(e, "job.started", job_id) for e in events)
    assert any(_event_matches(e, "job.deferred", job_id) for e in events)


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


def test_no_ollama_unload_without_flag():
    # Set VRAM low so it triggers recovery, but set ALLOW_OLLAMA_UNLOAD=false
    os.environ["MOCK_VRAM_FREE_MB"] = "3000"
    os.environ["MOCK_RAM_FREE_MB"] = "16000"
    os.environ["ALLOW_OLLAMA_UNLOAD"] = "false"
    os.environ["MOCK_OLLAMA_UNLOAD"] = "true"
    os.environ["MOCK_VRAM_FREED_MB"] = "4000"

    payload = {
        "schema_version": "bridge.command.v1",
        "command_type": "meshroom.photogrammetry_reconstruct",
        "target": "meshroom",
        "dry_run": False,
        "payload": {"images_dir": "test_input"}
    }

    response = client.post("/api/bridge/command", json=payload)
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    job_state = wait_for_job_completion(job_id)
    assert job_state["state"] == "deferred"
    assert "insufficient_vram" in job_state["error"]

    events = client.get("/events?limit=50").json()
    ollama_events = [
        e for e in events 
        if (e.get("type") or e.get("event")) == "job.ollama_unloaded"
        and (e.get("data") if isinstance(e.get("data"), dict) else e).get("job_id") == job_id
    ]
    assert len(ollama_events) == 0

    for key in ("MOCK_VRAM_FREE_MB", "MOCK_RAM_FREE_MB", "ALLOW_OLLAMA_UNLOAD", "MOCK_OLLAMA_UNLOAD", "MOCK_VRAM_FREED_MB"):
        if key in os.environ:
            del os.environ[key]


@patch("orchestrator.main.run_meshroom_pipeline")
def test_ollama_unload_single_attempt_recovery(mock_meshroom):
    mock_meshroom.return_value = {
        "success": True,
        "artifacts": ["artifacts/jobs/meshroom_reconstruction_test.obj"],
    }
    os.environ["MOCK_VRAM_FREE_MB"] = "3000"
    os.environ["MOCK_RAM_FREE_MB"] = "16000"
    os.environ["ALLOW_OLLAMA_UNLOAD"] = "true"
    os.environ["MOCK_OLLAMA_UNLOAD"] = "true"
    os.environ["MOCK_VRAM_FREED_MB"] = "4000"

    payload = {
        "schema_version": "bridge.command.v1",
        "command_type": "meshroom.photogrammetry_reconstruct",
        "target": "meshroom",
        "dry_run": False,
        "payload": {"images_dir": "test_input"}
    }

    response = client.post("/api/bridge/command", json=payload)
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    job_state = wait_for_job_completion(job_id, timeout=3.0)
    assert job_state["state"] in ("completed", "succeeded")

    for key in ("MOCK_VRAM_FREE_MB", "MOCK_RAM_FREE_MB", "ALLOW_OLLAMA_UNLOAD", "MOCK_OLLAMA_UNLOAD", "MOCK_VRAM_FREED_MB"):
        if key in os.environ:
            del os.environ[key]


def test_insufficient_vram_no_job_started():
    os.environ["MOCK_VRAM_FREE_MB"] = "1000"
    os.environ["MOCK_RAM_FREE_MB"] = "16000"

    payload = {
        "schema_version": "bridge.command.v1",
        "command_type": "blender.render_scene",
        "target": "blender",
        "dry_run": False,
        "payload": {"model_name": "StressSphere"},
    }

    response = client.post("/api/bridge/command", json=payload)
    job_id = response.json()["job_id"]
    job_state = wait_for_job_completion(job_id)

    assert job_state["state"] == "deferred"

    events = client.get("/events?limit=50").json()
    started_events = [
        e for e in events
        if (e.get("type") or e.get("event")) == "job.started"
        and (e.get("data") if isinstance(e.get("data"), dict) else e).get("job_id") == job_id
    ]
    assert len(started_events) == 0

    for key in ("MOCK_VRAM_FREE_MB", "MOCK_RAM_FREE_MB"):
        if key in os.environ:
            del os.environ[key]
