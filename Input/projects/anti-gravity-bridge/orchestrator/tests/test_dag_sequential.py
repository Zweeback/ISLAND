"""
test_dag_sequential.py - Phase 5 DAG unit tests.

Uses asyncio.run() in sync test functions to match existing test patterns
in this project (no pytest-asyncio required).

Tests:
  1. Full successful sequential run (mesh -> blend -> unity)
  2. First node failure => downstream nodes skipped
  3. Artifact handoff recorded per node
  4. No parallel execution (strictly 1 job in flight at a time)
  5. Middle-node failure => only downstream is skipped
"""
from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_dag(run_id: str = None):
    from orchestrator.dag_models import DagNode, DagRun

    run_id = run_id or "run_" + uuid.uuid4().hex[:8]
    return DagRun(
        run_id=run_id,
        nodes=[
            DagNode(
                node_id="mesh",
                command_type="meshroom.photogrammetry_reconstruct",
                target="meshroom",
                payload_template={},
            ),
            DagNode(
                node_id="blend",
                command_type="blender.create_cube",
                target="blender",
                depends_on=["mesh"],
                payload_template={},
            ),
            DagNode(
                node_id="unity",
                command_type="unity.sync_assets",
                target="unity",
                depends_on=["blend"],
                payload_template={},
            ),
        ],
        node_states={},
        artifacts={},
        provenance={},
    )


def _write_job_state(jobs_dir: Path, job_id: str, state: str, target: str, artifacts: list):
    job_dir = jobs_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "job_id": job_id,
        "state": state,
        "target": target,
        "command_type": "test.cmd",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:01Z",
        "artifacts": artifacts,
    }
    (job_dir / "job_state.json").write_text(json.dumps(data), encoding="utf-8")


# ---------------------------------------------------------------------------
# Tests  (all synchronous - use asyncio.run)
# ---------------------------------------------------------------------------

def test_successful_sequential(tmp_path, monkeypatch):
    """All three nodes complete in order; artifact paths recorded."""
    import orchestrator.main as m

    tmp_jobs = tmp_path / "jobs"
    monkeypatch.setattr(m, "JOBS_DIR", tmp_jobs)
    monkeypatch.setattr(m, "generate_provenance", lambda **_kw: None)

    call_order = []

    async def mock_run_job(cmd, job_id):
        call_order.append(cmd.target)
        art = f"artifacts/jobs/{job_id}/output_{cmd.target}.txt"
        _write_job_state(tmp_jobs, job_id, "completed", cmd.target, [art])

    monkeypatch.setattr(m, "run_job", mock_run_job)

    from orchestrator.dag_executor import execute_dag
    result = asyncio.run(execute_dag(_make_dag()))

    assert result.node_states == {"mesh": "completed", "blend": "completed", "unity": "completed"}
    assert call_order == ["meshroom", "blender", "unity"], f"Wrong order: {call_order}"
    for nid in ("mesh", "blend", "unity"):
        assert nid in result.artifacts


def test_first_node_failure_skips_downstream(tmp_path, monkeypatch):
    """Meshroom failure => blender and unity are skipped, never invoked."""
    import orchestrator.main as m

    tmp_jobs = tmp_path / "jobs"
    monkeypatch.setattr(m, "JOBS_DIR", tmp_jobs)
    monkeypatch.setattr(m, "generate_provenance", lambda **_kw: None)

    ran_targets = []

    async def mock_run_job(cmd, job_id):
        ran_targets.append(cmd.target)
        state = "failed" if cmd.target == "meshroom" else "completed"
        _write_job_state(tmp_jobs, job_id, state, cmd.target, [])

    monkeypatch.setattr(m, "run_job", mock_run_job)

    from orchestrator.dag_executor import execute_dag
    result = asyncio.run(execute_dag(_make_dag()))

    assert result.node_states["mesh"] == "failed"
    assert result.node_states["blend"] == "skipped"
    assert result.node_states["unity"] == "skipped"
    assert ran_targets == ["meshroom"], f"Expected only meshroom to run, got: {ran_targets}"


def test_artifact_handoff_recorded(tmp_path, monkeypatch):
    """Each completed node records a unique artifact path in dag.artifacts."""
    import orchestrator.main as m

    tmp_jobs = tmp_path / "jobs"
    monkeypatch.setattr(m, "JOBS_DIR", tmp_jobs)
    monkeypatch.setattr(m, "generate_provenance", lambda **_kw: None)

    async def mock_run_job(cmd, job_id):
        art = f"artifacts/jobs/{job_id}/{cmd.target}_out.obj"
        _write_job_state(tmp_jobs, job_id, "completed", cmd.target, [art])

    monkeypatch.setattr(m, "run_job", mock_run_job)

    from orchestrator.dag_executor import execute_dag
    result = asyncio.run(execute_dag(_make_dag()))

    assert len(result.artifacts) == 3
    assert len(set(result.artifacts.values())) == 3  # all unique paths
    for nid, path in result.artifacts.items():
        assert nid in ("mesh", "blend", "unity")
        assert path.endswith(".obj")


def test_no_parallel_execution(tmp_path, monkeypatch):
    """At most 1 job runs concurrently at any point in time."""
    import orchestrator.main as m

    tmp_jobs = tmp_path / "jobs"
    monkeypatch.setattr(m, "JOBS_DIR", tmp_jobs)
    monkeypatch.setattr(m, "generate_provenance", lambda **_kw: None)

    in_flight = []
    max_concurrent = [0]

    async def mock_run_job(cmd, job_id):
        in_flight.append(cmd.target)
        max_concurrent[0] = max(max_concurrent[0], len(in_flight))
        _write_job_state(tmp_jobs, job_id, "completed", cmd.target, [])
        in_flight.remove(cmd.target)

    monkeypatch.setattr(m, "run_job", mock_run_job)

    from orchestrator.dag_executor import execute_dag
    asyncio.run(execute_dag(_make_dag()))

    assert max_concurrent[0] == 1, f"Expected max 1 concurrent job, got {max_concurrent[0]}"


def test_deferred_node_skips_downstream(tmp_path, monkeypatch):
    """Meshroom deferred (VRAM) => downstream skipped, not treated as hard failed."""
    import orchestrator.main as m

    tmp_jobs = tmp_path / "jobs"
    monkeypatch.setattr(m, "JOBS_DIR", tmp_jobs)
    monkeypatch.setattr(m, "generate_provenance", lambda **_kw: None)

    ran_targets = []

    async def mock_run_job(cmd, job_id):
        ran_targets.append(cmd.target)
        _write_job_state(tmp_jobs, job_id, "deferred", cmd.target, [])

    monkeypatch.setattr(m, "run_job", mock_run_job)

    from orchestrator.dag_executor import execute_dag
    result = asyncio.run(execute_dag(_make_dag()))

    assert result.node_states["mesh"] == "deferred"
    assert result.node_states["blend"] == "skipped"
    assert result.node_states["unity"] == "skipped"
    assert ran_targets == ["meshroom"]


def test_middle_node_failure(tmp_path, monkeypatch):
    """Blender failure => unity is skipped; meshroom stays completed."""
    import orchestrator.main as m

    tmp_jobs = tmp_path / "jobs"
    monkeypatch.setattr(m, "JOBS_DIR", tmp_jobs)
    monkeypatch.setattr(m, "generate_provenance", lambda **_kw: None)

    async def mock_run_job(cmd, job_id):
        state = "failed" if cmd.target == "blender" else "completed"
        _write_job_state(tmp_jobs, job_id, state, cmd.target, [])

    monkeypatch.setattr(m, "run_job", mock_run_job)

    from orchestrator.dag_executor import execute_dag
    result = asyncio.run(execute_dag(_make_dag()))

    assert result.node_states["mesh"] == "completed"
    assert result.node_states["blend"] == "failed"
    assert result.node_states["unity"] == "skipped"
