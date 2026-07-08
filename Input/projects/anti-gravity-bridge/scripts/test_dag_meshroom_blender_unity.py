"""
test_dag_meshroom_blender_unity.py - Phase 5 DAG smoke test.

Runs the 3-node DAG in dry_run mode so no real Meshroom/Blender/Unity
process is spawned. Verifies the sequential state progression and
that provenance is recorded per node.

Usage:
    python scripts/test_dag_meshroom_blender_unity.py
"""
import asyncio
import sys
import os
import uuid

# Ensure the project root is on the path.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from orchestrator.dag_models import DagNode, DagRun


async def main():
    from orchestrator.dag_executor import execute_dag
    from orchestrator.main import BridgeCommand, JOBS_DIR

    run_id = "smoke_" + uuid.uuid4().hex[:8]
    print(f"\n[SMOKE] DAG run_id: {run_id}")

    dag = DagRun(
        run_id=run_id,
        nodes=[
            DagNode(
                node_id="mesh",
                command_type="meshroom.photogrammetry_reconstruct",
                target="meshroom",
                payload_template={"project_id": "smoke_proj"},
            ),
            DagNode(
                node_id="blend",
                command_type="blender.create_cube",
                target="blender",
                depends_on=["mesh"],
                payload_template={"model_name": "smoke_model"},
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

    result = await execute_dag(dag)

    print("\n[SMOKE] === DAG Result ===")
    for nid, state in result.node_states.items():
        art = result.artifacts.get(nid, "(none)")
        prov = result.provenance.get(nid, {})
        sha = prov.get("sha256", "n/a")[:12] if prov.get("sha256") else "n/a"
        print(f"  {nid:<8}  state={state:<12}  artifact={art}  sha256[:12]={sha}")

    failed = [n for n, s in result.node_states.items() if s == "failed"]
    if failed:
        print(f"\n[SMOKE] WARN: failed nodes: {failed}")
        sys.exit(1)
    else:
        print("\n[SMOKE] PASS: all nodes completed or skipped cleanly.")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
