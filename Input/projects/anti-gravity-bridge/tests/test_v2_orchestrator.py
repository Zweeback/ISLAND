import os
import json
import time
from fastapi.testclient import TestClient
from orchestrator.main import app

client = TestClient(app)

def test_v2_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "operational")
    assert data["service"] == "anti-gravity-bridge"
    assert "capabilities_total" in data

def test_v2_capabilities_endpoint():
    response = client.get("/capabilities")
    assert response.status_code == 200
    capabilities = response.json()
    assert len(capabilities) >= 3
    # Check that keys are mapped to Pydantic Cap schema
    cap_ids = [c["id"] for c in capabilities]
    assert "unity.sync_assets" in cap_ids
    assert "blender.render_scene" in cap_ids

def test_v2_command_dispatch_and_status():
    # Post a valid dry_run command
    payload = {
        "schema_version": "bridge.command.v1",
        "command_id": "cmd_test_v2_123",
        "command_type": "blender.render_scene",
        "target": "blender",
        "dry_run": True,
        "payload": {"model_name": "TestSphere", "engine": "CYCLES"}
    }

    response = client.post("/api/bridge/command", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] is True
    job_id = data["job_id"]
    assert job_id is not None
    assert data["command_id"] == "cmd_test_v2_123"

    # Give the background task a tiny slice to execute
    time.sleep(0.1)

    # Get job status
    status_response = client.get(f"/jobs/{job_id}")
    assert status_response.status_code == 200
    job_state = status_response.json()
    assert job_state["job_id"] == job_id
    assert job_state["state"] in ("accepted", "running", "completed")

    # Read events to check if job events were recorded
    events_response = client.get("/events")
    assert events_response.status_code == 200
    events = events_response.json()
    assert len(events) > 0
    event_types = [e["type"] for e in events]
    assert "job.accepted" in event_types

def test_v2_validation_error():
    # Post invalid schema version
    payload = {
        "schema_version": "invalid_version",
        "command_type": "blender.render_scene",
        "target": "blender",
        "payload": {}
    }
    response = client.post("/api/bridge/command", json=payload)
    assert response.status_code == 422 # Pydantic validation error

def test_v2_websocket_events():
    with client.websocket_connect("/ws/events") as websocket:
        payload = {
            "schema_version": "bridge.command.v1",
            "command_id": "cmd_ws_test_456",
            "command_type": "unity.create_primitive",
            "target": "unity",
            "dry_run": True,
            "payload": {"primitive": "Cube"}
        }
        response = client.post("/api/bridge/command", json=payload)
        assert response.status_code == 202
        job_id = response.json()["job_id"]

        # Read the event from the websocket
        event1 = websocket.receive_json()
        assert event1["type"] == "job.accepted"
        assert event1["job_id"] == job_id
