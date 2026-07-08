import os
import json
import tempfile
import pytest
from orchestrator.capabilities import CapabilityRegistry, Capability
from orchestrator.state_machine import JobStateMachine, ALLOWED_TRANSITIONS
from orchestrator.provenance import generate_provenance, compute_sha256, get_git_commit, get_tool_versions
from orchestrator.event_logger import EventLogger

def test_capability_parsing():
    registry = CapabilityRegistry()
    caps = registry.list_capabilities()
    assert len(caps) >= 3

    blender_cap = registry.get_capability("blender.render_scene")
    assert blender_cap is not None
    assert blender_cap.version == "1.0.0"
    assert blender_cap.resource_requirements.cpu_cores == 2
    assert blender_cap.resource_requirements.gpu_required is False

def test_state_transitions():
    job_id = "test-job-sm-1"

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    state_file = os.path.join(base_dir, "artifacts", "jobs", job_id, "job_state.json")
    if os.path.exists(state_file):
        try:
            os.remove(state_file)
        except Exception:
            pass

    sm = JobStateMachine(job_id, initial_state="queued")
    assert sm.state == "queued"
    assert len(sm.history) == 1
    assert sm.history[0]["state"] == "queued"

    sm.transition_to("validating", reason="Testing transition")
    assert sm.state == "validating"
    assert len(sm.history) == 2

    with pytest.raises(ValueError):
        sm.transition_to("succeeded")

    sm.transition_to("ready")
    sm.transition_to("running")
    sm.transition_to("succeeded")
    assert sm.state == "succeeded"

    sm_reload = JobStateMachine(job_id)
    assert sm_reload.state == "succeeded"
    assert len(sm_reload.history) == 5

def test_provenance_generation():
    job_id = "test-job-prov-1"

    with tempfile.NamedTemporaryFile(delete=False) as f_in, tempfile.NamedTemporaryFile(delete=False) as f_out:
        f_in.write(b"Hello World Input")
        f_in_name = f_in.name

        f_out.write(b"Hello World Output")
        f_out_name = f_out.name

    try:
        command = {"action": "test", "payload": {"foo": "bar"}}
        prov = generate_provenance(
            job_id=job_id,
            command=command,
            input_files=[f_in_name],
            output_files=[f_out_name]
        )

        assert prov["job_id"] == job_id
        assert prov["command"] == command
        assert len(prov["input_hashes"]) == 1
        assert len(prov["output_hashes"]) == 1
        assert prov["input_hashes"][f_in_name] == compute_sha256(f_in_name)
        assert prov["output_hashes"][f_out_name] == compute_sha256(f_out_name)
        assert "git_commit" in prov
        assert "python_version" in prov
        assert "os" in prov
        assert "tool_versions" in prov

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        prov_file = os.path.join(base_dir, "artifacts", "jobs", job_id, "provenance.json")
        assert os.path.exists(prov_file)
        with open(prov_file, "r") as pf:
            data = json.load(pf)
            assert data["job_id"] == job_id
    finally:
        if os.path.exists(f_in_name):
            try:
                os.remove(f_in_name)
            except Exception:
                pass
        if os.path.exists(f_out_name):
            try:
                os.remove(f_out_name)
            except Exception:
                pass

def test_event_append_only():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl") as temp_log:
        temp_log_path = temp_log.name

    try:
        logger = EventLogger(log_file=temp_log_path)
        logger.log_event("CommandReceived", {"cmd": "val1"})
        logger.log_event("CommandValidated", {"cmd": "val1", "valid": True})

        with open(temp_log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        assert len(lines) == 2
        ev1 = json.loads(lines[0])
        ev2 = json.loads(lines[1])

        assert ev1["event"] == "CommandReceived"
        assert ev1["data"]["cmd"] == "val1"
        assert ev2["event"] == "CommandValidated"
        assert ev2["data"]["valid"] is True
    finally:
        if os.path.exists(temp_log_path):
            try:
                os.remove(temp_log_path)
            except Exception:
                pass
