import os
import subprocess
import logging
import shutil
import json
from typing import Dict, Any

logger = logging.getLogger("anti-gravity-bridge.blender")

def run_blender_command(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes a Blender command headless using sandboxed bridge_worker.py allowlisted commands.
    If the 'blender' executable is not found or is in dry-run mode,
    it performs a mock operation and outputs mock artifacts to simulate success.
    """
    logger.info(f"Running Blender Action: {action} with Payload: {payload}")

    # Check if a custom blender path is provided, otherwise fall back to system 'blender'
    blender_exe = os.getenv("BLENDER_PATH", "blender")
    dry_run = os.getenv("BLENDER_DRY_RUN", "true").lower() in ("true", "1", "yes")

    # Resolve paths relative to the bridge workspace
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    artifacts_jobs_dir = os.path.join(base_dir, "artifacts", "jobs")
    os.makedirs(artifacts_jobs_dir, exist_ok=True)

    if dry_run or not shutil.which(blender_exe):
        logger.warning("Blender executable not found or running in DRY_RUN mode. Simulating rendering...")

        # Simulate generating a rendered model / image artifact
        artifact_filename = f"blender_job_{action}_{payload.get('model_name', 'model')}.glb"
        artifact_path = os.path.join("artifacts", "jobs", artifact_filename)
        absolute_artifact_path = os.path.join(artifacts_jobs_dir, artifact_filename)

        # Write mock GLB file content
        with open(absolute_artifact_path, "w") as f:
            f.write(f"MOCK GLB DATA FOR ACTION {action}\n")
            f.write(f"Model: {payload.get('model_name', 'DefaultCube')}\n")
            f.write(f"Format: GLTF/GLB\n")
            f.write(f"Render engine: {payload.get('engine', 'CYCLES')}\n")

        return {
            "success": True,
            "message": f"Blender dry-run simulated successfully for action '{action}'.",
            "artifacts": [artifact_path.replace("\\", "/")]
        }

    # Real Blender Invocation using sandboxed bridge_worker.py
    worker_script = os.path.join(base_dir, "blender", "bridge_worker.py")

    # Create output GLB file path
    output_filename = f"blender_{action}.glb"
    output_path = os.path.join(artifacts_jobs_dir, output_filename).replace("\\", "/")

    # Generate allowlisted commands
    commands = [
        {"command": "clear_scene"},
    ]

    # Add creation command
    primitive = payload.get("primitive", "Cube")
    if primitive.lower() in ("cube", "box"):
        scale = payload.get("scale", [1.0, 1.0, 1.0])
        commands.append({"command": "create_cube", "scale": scale})
    elif primitive.lower() == "sphere":
        radius = payload.get("radius", 1.0)
        commands.append({"command": "create_uv_sphere", "radius": radius})
    else:
        commands.append({"command": "create_cube", "scale": [1.0, 1.0, 1.0]})

    # Add export command
    commands.append({"command": "export_scene_glb", "output_path": output_path})

    try:
        stdout_log = []
        for cmd_dict in commands:
            cmd_json_file = os.path.join(artifacts_jobs_dir, "blender_cmd.json")
            with open(cmd_json_file, "w", encoding="utf-8") as f:
                json.dump(cmd_dict, f)

            cmd = [blender_exe, "--background", "--python", worker_script, "--", cmd_json_file]
            logger.info(f"Executing sandboxed command: {' '.join(cmd)}")

            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60
            )

            # Clean up JSON command file
            if os.path.exists(cmd_json_file):
                try:
                    os.remove(cmd_json_file)
                except Exception:
                    pass

            if process.returncode != 0:
                return {
                    "success": False,
                    "error": f"Blender command {cmd_dict['command']} failed with code {process.returncode}",
                    "stderr": process.stderr
                }
            stdout_log.append(process.stdout)

        exported_rel_path = os.path.join("artifacts", "jobs", output_filename).replace("\\", "/")
        return {
            "success": True,
            "message": "Blender sandboxed execution completed successfully.",
            "stdout": "\n".join(stdout_log),
            "artifacts": [exported_rel_path]
        }

    except Exception as e:
        logger.error(f"Error executing Blender subprocess: {e}")
        return {
            "success": False,
            "error": str(e)
        }
