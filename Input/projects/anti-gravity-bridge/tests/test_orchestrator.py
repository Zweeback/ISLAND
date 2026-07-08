import os
import json
import time
from fastapi.testclient import TestClient
from orchestrator.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "operational")
    assert data["service"] == "anti-gravity-bridge"
    assert data["capabilities_total"] >= 3

def test_capabilities_endpoint():
    response = client.get("/capabilities")
    assert response.status_code == 200
    capabilities = response.json()
    ids = {cap["id"] for cap in capabilities}
    assert "unity.sync_assets" in ids
    assert "blender.render_scene" in ids
    assert "meshroom.photogrammetry_reconstruct" in ids

def test_command_routing_validation():
    # 1. Valid command targeting unity
    payload = {
        "schema_version": "bridge.command.v1",
        "command_id": "test-uuid-1",
        "command_type": "unity.rebuild_lighting",
        "target": "unity",
        "payload": {"intensity": 1.2}
    }
    response = client.post("/api/bridge/command", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] is True
    assert data["command_id"] == "test-uuid-1"

    # 2. Invalid target should trigger 422 Unprocessable Entity in Pydantic v2
    invalid_target = payload.copy()
    invalid_target["target"] = "unreal_engine"
    response = client.post("/api/bridge/command", json=invalid_target)
    assert response.status_code == 422

def test_jobs_lifecyle():
    # 1. Create a background rendering job
    job_req = {
        "schema_version": "bridge.command.v1",
        "command_type": "blender.render_scene",
        "target": "blender",
        "dry_run": True,
        "payload": {
            "model_name": "TestSphere",
            "engine": "EVEE"
        }
    }
    response = client.post("/api/bridge/command", json=job_req)
    assert response.status_code == 202
    data = response.json()
    job_id = data["job_id"]
    assert job_id is not None

    # Wait for the async task to execute
    time.sleep(0.1)

    # 2. Query specific job status
    query_response = client.get(f"/jobs/{job_id}")
    assert query_response.status_code == 200
    assert query_response.json()["job_id"] == job_id

    provenance_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "artifacts",
        "jobs",
        job_id,
        "provenance.json"
    )
    assert os.path.exists(provenance_path)

def test_events_endpoint_is_append_only_readable():
    response = client.get("/events")
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
