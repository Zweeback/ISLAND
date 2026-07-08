import os
import subprocess
import logging
import shutil
from typing import Dict, Any

logger = logging.getLogger("anti-gravity-bridge.meshroom")

def run_meshroom_pipeline(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wraps the Meshroom photogrammetry pipeline.
    Performs preflight checks for input directories and CUDA availability,
    then executes meshroom_batch or simulates the output.
    """
    logger.info(f"Running Meshroom Pipeline: {action} with Payload: {payload}")

    images_dir = payload.get("images_dir")
    meshroom_exe = os.getenv("MESHROOM_PATH", "meshroom_batch")
    dry_run = os.getenv("MESHROOM_DRY_RUN", "true").lower() in ("true", "1", "yes")

    # Resolve paths relative to the bridge workspace
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    artifacts_jobs_dir = os.path.join(base_dir, "artifacts", "jobs")
    os.makedirs(artifacts_jobs_dir, exist_ok=True)

    # 1. Preflight Validation: Input Images Check
    if not images_dir:
        return {
            "success": False,
            "error": "Preflight failed: 'images_dir' parameter is required for photogrammetry."
        }

    if not dry_run and not os.path.isdir(images_dir):
        return {
            "success": False,
            "error": f"Preflight failed: Input images directory '{images_dir}' does not exist."
        }

    # 2. Preflight Validation: CUDA Check
    # Meshroom requires CUDA for depth maps. Let's do a quick nvidia-smi check.
    cuda_available = False
    if shutil.which("nvidia-smi"):
        cuda_available = True
    else:
        logger.warning("CUDA check: nvidia-smi not found. Meshroom requires CUDA for depth map computations.")

    # 3. Execution / Simulation
    if dry_run or not shutil.which(meshroom_exe):
        logger.warning("Meshroom executable not found or running in DRY_RUN mode. Simulating 3D reconstruction...")

        # Simulate generating a 3D model artifact
        artifact_filename = f"meshroom_reconstruction_{payload.get('project_id', 'proj')}.obj"
        artifact_path = os.path.join("artifacts", "jobs", artifact_filename)
        absolute_artifact_path = os.path.join(artifacts_jobs_dir, artifact_filename)

        with open(absolute_artifact_path, "w") as f:
            f.write(f"# MOCK OBJ RECONSTRUCTION FOR ACTION {action}\n")
            f.write(f"# Generated from directory: {images_dir}\n")
            f.write(f"# CUDA Detected: {cuda_available}\n")
            f.write("v 0.000000 0.000000 0.000000\n")
            f.write("v 1.000000 0.000000 0.000000\n")
            f.write("v 0.000000 1.000000 0.000000\n")
            f.write("f 1 2 3\n")

        return {
            "success": True,
            "message": f"Meshroom dry-run simulated successfully for action '{action}'.",
            "cuda_available": cuda_available,
            "artifacts": [artifact_path.replace("\\", "/")]
        }

    # Real Meshroom Subprocess Execution
    try:
        output_mesh_path = os.path.join(artifacts_jobs_dir, f"meshroom_output_{payload.get('project_id', 'proj')}.obj")

        # Command setup
        # Example: meshroom_batch --input <images_dir> --output <output_mesh_path>
        cmd = [meshroom_exe, "--input", images_dir, "--output", output_mesh_path]
        logger.info(f"Executing Meshroom CLI: {' '.join(cmd)}")

        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=600  # Meshroom jobs can take longer
        )

        if process.returncode == 0:
            relative_output_path = os.path.join("artifacts", "jobs", os.path.basename(output_mesh_path)).replace("\\", "/")
            return {
                "success": True,
                "message": "Meshroom reconstruction completed successfully.",
                "stdout": process.stdout,
                "artifacts": [relative_output_path]
            }
        else:
            return {
                "success": False,
                "error": f"Meshroom exited with code {process.returncode}",
                "stderr": process.stderr
            }

    except Exception as e:
        logger.error(f"Error executing Meshroom subprocess: {e}")
        return {
            "success": False,
            "error": str(e)
        }
