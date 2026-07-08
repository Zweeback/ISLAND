"""
dag_executor.py - Minimal sequential DAG executor for Phase 5.

Executes a DagRun node-by-node in topological (dependency) order.
No parallel scheduling. No external graph libs.
Integrates with the existing Bridge job infrastructure via run_job().
"""
from __future__ import annotations

import json
import uuid
import hashlib
import logging
from pathlib import Path
from typing import Dict, List

log = logging.getLogger("anti-gravity-bridge.dag")


async def execute_dag(dag) -> object:
    """Execute *dag* sequentially, respecting dependencies.

    Updates dag.node_states and dag.artifacts in place and returns the dag.
    """
    # Late imports avoid circular-import; main is fully loaded by this point.
    from orchestrator.main import (
        run_job,
        BridgeCommand,
        JOBS_DIR,
        generate_provenance,
        append_event,
        bus,
    )

    node_states: Dict[str, str] = {n.node_id: "pending" for n in dag.nodes}
    artifacts: Dict[str, str] = {}

    def _load_job_state(job_id: str) -> Dict:
        path = JOBS_DIR / job_id / "job_state.json"
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    async def _emit(event: Dict) -> None:
        append_event(event)
        await bus.broadcast(event)

    # Topological sweep - loop until no more progress can be made.
    progress = True
    while progress:
        progress = False
        for node in dag.nodes:
            nid = node.node_id
            if node_states[nid] != "pending":
                continue  # already settled

            # If any dependency failed/skipped, skip this node too.
            if any(node_states.get(dep) in ("failed", "skipped") for dep in node.depends_on):
                node_states[nid] = "skipped"
                await _emit({"type": "dag.node_skipped", "run_id": dag.run_id, "node_id": nid})
                progress = True
                continue

            # Not all deps completed yet - wait next sweep.
            if not all(node_states.get(dep) == "completed" for dep in node.depends_on):
                continue

            # All deps satisfied - run this node.
            node_states[nid] = "running"
            progress = True
            job_id = f"{dag.run_id}_{nid}_{uuid.uuid4().hex[:8]}"
            await _emit({"type": "dag.node_started", "run_id": dag.run_id, "node_id": nid, "job_id": job_id})

            cmd = BridgeCommand(
                command_type=node.command_type,
                target=node.target,
                dry_run=False,
                priority=50,
                payload=dict(node.payload_template),
                constraints={},
                provenance={"dag_run_id": dag.run_id, "node_id": nid},
            )
            await run_job(cmd, job_id)

            job_state = _load_job_state(job_id)
            raw_state: str = job_state.get("state") or job_state.get("current_state") or "failed"
            final_state = "completed" if raw_state == "completed" else "failed"
            node_states[nid] = final_state

            art_list: List[str] = job_state.get("artifacts", [])
            if art_list:
                first_art = art_list[0]
                artifacts[nid] = first_art
                art_path = Path(first_art)
                sha = hashlib.sha256(art_path.read_bytes()).hexdigest() if art_path.exists() else hashlib.sha256(first_art.encode()).hexdigest()
                dag.provenance[nid] = {"artifact": first_art, "sha256": sha, "job_id": job_id}
            else:
                dag.provenance[nid] = {"artifact": None, "job_id": job_id}

            await _emit({
                "type": f"dag.node_{final_state}",
                "run_id": dag.run_id,
                "node_id": nid,
                "job_id": job_id,
                "artifacts": art_list,
            })

    # Any node still pending has no reachable path - mark skipped.
    for n in dag.nodes:
        if node_states[n.node_id] == "pending":
            node_states[n.node_id] = "skipped"

    dag.node_states = node_states
    dag.artifacts = artifacts

    generate_provenance(
        job_id=dag.run_id,
        command={"dag_run_id": dag.run_id, "nodes": [n.node_id for n in dag.nodes]},
        input_files=[],
        output_files=list(artifacts.values()),
    )

    overall = "completed" if all(s in ("completed", "skipped") for s in node_states.values()) else "failed"
    log.info("DAG %s finished: %s  states=%s", dag.run_id, overall, node_states)
    return dag
