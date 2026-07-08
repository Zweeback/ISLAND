import os
import time
import asyncio
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from orchestrator.main import app, retry_deferred_entry
from orchestrator.deferred_queue import (
    DEFERRED_DIR,
    load_deferred_entry,
    remove_deferred_entry,
    queue_depth,
)
from orchestrator.retry_scheduler import process_deferred_once, is_dispatching

client = TestClient(app)

MOCK_ENV_KEYS = (
    "MOCK_VRAM_FREE_MB",
    "MOCK_RAM_FREE_MB",
    "MOCK_OLLAMA_UNLOAD",
    "MOCK_VRAM_FREED_MB",
    "ALLOW_OLLAMA_UNLOAD",
    "DEFERRED_MAX_RETRIES",
    "DEFERRED_BACKOFF_BASE_SEC",
    "DEFERRED_RETRY_INTERVAL_SEC",
)


@pytest.fixture(autouse=True)
def clean_env():
    os.environ["DISABLE_DEFERRED_SCHEDULER"] = "true"
    if DEFERRED_DIR.exists():
        for path in DEFERRED_DIR.glob("*.json"):
            path.unlink()
    for key in MOCK_ENV_KEYS:
        os.environ.pop(key, None)
    yield
    if DEFERRED_DIR.exists():
        for path in DEFERRED_DIR.glob("*.json"):
            path.unlink()
    for key in MOCK_ENV_KEYS:
        os.environ.pop(key, None)
    os.environ.pop("DISABLE_DEFERRED_SCHEDULER", None)


def _event_matches(job_event: dict, event_type: str, target_job_id: str) -> bool:
    event_kind = job_event.get("type") or job_event.get("event")
    if event_kind != event_type:
        return False
    payload = job_event.get("data") if isinstance(job_event.get("data"), dict) else job_event
    return payload.get("job_id") == target_job_id


def _job_events(job_id: str, limit: int = 100) -> list:
    return client.get(f"/events?limit={limit}").json()


def wait_for_state(job_id: str, wanted: set[str], timeout: float = 3.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        res = client.get(f"/jobs/{job_id}")
        data = res.json()
        if data.get("state") in wanted:
            return data
        time.sleep(0.05)
    return client.get(f"/jobs/{job_id}").json()


def test_insufficient_vram_sets_deferred_state():
    os.environ["MOCK_VRAM_FREE_MB"] = "1000"
    os.environ["MOCK_RAM_FREE_MB"] = "16000"

    response = client.post(
        "/api/bridge/command",
        json={
            "schema_version": "bridge.command.v1",
            "command_type": "meshroom.photogrammetry_reconstruct",
            "target": "meshroom",
            "dry_run": False,
            "payload": {"images_dir": "test_input"},
        },
    )
    job_id = response.json()["job_id"]
    job_state = wait_for_state(job_id, {"deferred"})

    assert job_state["state"] == "deferred"
    assert "insufficient_vram" in job_state["error"]
    assert load_deferred_entry(job_id) is not None
    assert queue_depth() >= 1

    events = _job_events(job_id)
    assert any(_event_matches(e, "job.deferred", job_id) for e in events)
    assert not any(_event_matches(e, "job.started", job_id) for e in events)
    assert not any(_event_matches(e, "job.failed", job_id) for e in events)

    history = [h["state"] for h in job_state.get("history", [])]
    assert "running" not in history
    assert history[-1] == "deferred"


@patch("orchestrator.main.run_meshroom_pipeline")
def test_deferred_job_retries_when_vram_available(mock_meshroom):
    mock_meshroom.return_value = {
        "success": True,
        "artifacts": ["artifacts/jobs/meshroom_reconstruction_test.obj"],
    }
    os.environ["MOCK_VRAM_FREE_MB"] = "1000"
    os.environ["MOCK_RAM_FREE_MB"] = "16000"

    response = client.post(
        "/api/bridge/command",
        json={
            "schema_version": "bridge.command.v1",
            "command_type": "meshroom.photogrammetry_reconstruct",
            "target": "meshroom",
            "dry_run": False,
            "payload": {"images_dir": "test_input"},
        },
    )
    job_id = response.json()["job_id"]
    wait_for_state(job_id, {"deferred"})

    os.environ["MOCK_VRAM_FREE_MB"] = "8000"
    entry = load_deferred_entry(job_id)
    assert entry is not None

    asyncio.run(retry_deferred_entry(entry))

    job_state = wait_for_state(job_id, {"completed", "succeeded"}, timeout=5.0)
    assert job_state["state"] in ("completed", "succeeded")
    assert load_deferred_entry(job_id) is None

    events = _job_events(job_id)
    assert any(_event_matches(e, "job.retrying", job_id) for e in events)
    assert any(_event_matches(e, "job.started", job_id) for e in events)
    mock_meshroom.assert_called_once()


def test_deferred_max_retries_exhausted():
    os.environ["MOCK_VRAM_FREE_MB"] = "1000"
    os.environ["MOCK_RAM_FREE_MB"] = "16000"
    os.environ["DEFERRED_MAX_RETRIES"] = "2"

    response = client.post(
        "/api/bridge/command",
        json={
            "schema_version": "bridge.command.v1",
            "command_type": "blender.render_scene",
            "target": "blender",
            "dry_run": False,
            "payload": {"model_name": "RetryExhaust"},
        },
    )
    job_id = response.json()["job_id"]
    wait_for_state(job_id, {"deferred"})

    for _ in range(3):
        entry = load_deferred_entry(job_id)
        if not entry:
            break
        entry["next_retry_at"] = "2000-01-01T00:00:00Z"
        from orchestrator.deferred_queue import save_deferred_entry

        save_deferred_entry(entry)
        asyncio.run(process_deferred_once(retry_deferred_entry))

    job_state = wait_for_state(job_id, {"failed"}, timeout=5.0)
    assert job_state["state"] == "failed"
    assert "retry_exhausted" in job_state["error"]
    assert load_deferred_entry(job_id) is None

    events = _job_events(job_id)
    assert any(_event_matches(e, "job.retry_exhausted", job_id) for e in events)


@patch("orchestrator.main.run_meshroom_pipeline")
def test_no_duplicate_dispatch_on_retry(mock_meshroom):
    mock_meshroom.return_value = {
        "success": True,
        "artifacts": ["artifacts/jobs/meshroom_reconstruction_test.obj"],
    }
    os.environ["MOCK_VRAM_FREE_MB"] = "1000"
    os.environ["MOCK_RAM_FREE_MB"] = "16000"

    response = client.post(
        "/api/bridge/command",
        json={
            "schema_version": "bridge.command.v1",
            "command_type": "meshroom.photogrammetry_reconstruct",
            "target": "meshroom",
            "dry_run": False,
            "payload": {"images_dir": "test_input"},
        },
    )
    job_id = response.json()["job_id"]
    wait_for_state(job_id, {"deferred"})
    os.environ["MOCK_VRAM_FREE_MB"] = "8000"

    entry = load_deferred_entry(job_id)
    entry["next_retry_at"] = "2000-01-01T00:00:00Z"
    from orchestrator.deferred_queue import save_deferred_entry

    save_deferred_entry(entry)

    from orchestrator.retry_scheduler import _dispatching

    _dispatching.add(job_id)
    asyncio.run(process_deferred_once(retry_deferred_entry))
    mock_meshroom.assert_not_called()

    _dispatching.discard(job_id)
    asyncio.run(process_deferred_once(retry_deferred_entry))
    assert mock_meshroom.call_count == 1
    remove_deferred_entry(job_id)