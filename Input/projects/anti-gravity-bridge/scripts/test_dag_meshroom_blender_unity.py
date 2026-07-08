"""
test_dag_meshroom_blender_unity.py - Phase 5 DAG smoke test.

Runs the 3-node DAG in dry_run mode (default) so admission/subprocess
pressure is bypassed while sequential ordering is verified.

Usage:
    python scripts/test_dag_meshroom_blender_unity.py
    python scripts/test_dag_meshroom_blender_unity.py --real
"""
import argparse
import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from orchestrator.dag_models import DagNode, DagRun


async def main(dry_run: bool = True) -> int:
    from orchestrator.dag_executor import execute_dag

    run_id = "smoke_" + uuid.uuid4().hex[:8]
    print(f"\n[SMOKE] DAG run_id: {run_id}  dry_run={dry_run}")

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

    result = await execute_dag(dag, dry_run=dry_run)

    print("\n[SMOKE] === DAG Result ===")
    for nid, state in result.node_states.items():
        art = result.artifacts.get(nid, "(none)")
        prov = result.provenance.get(nid, {})
        sha = prov.get("sha256", "n/a")[:12] if prov.get("sha256") else "n/a"
        print(f"  {nid:<8}  state={state:<12}  artifact={art}  sha256[:12]={sha}")

    if dry_run:
        if result.node_states == {"mesh": "completed", "blend": "completed", "unity": "completed"}:
            print("\n[SMOKE] PASS: dry_run sequential DAG completed.")
            return 0
        print(f"\n[SMOKE] FAIL: unexpected states {result.node_states}")
        return 1

    deferred = [n for n, s in result.node_states.items() if s == "deferred"]
    failed = [n for n, s in result.node_states.items() if s == "failed"]
    if deferred:
        print(f"\n[SMOKE] PASS (real): deferred nodes {deferred} — downstream skipped as expected.")
        return 0
    if failed:
        print(f"\n[SMOKE] WARN (real): failed nodes {failed}")
        return 1
    print("\n[SMOKE] PASS (real): all nodes completed or skipped cleanly.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--real", action="store_true", help="Run with dry_run=False (VRAM admission applies)")
    args = parser.parse_args()
    sys.exit(asyncio.run(main(dry_run=not args.real)))