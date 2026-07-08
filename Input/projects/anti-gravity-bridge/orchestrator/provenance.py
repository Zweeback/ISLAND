import os
import sys
import platform
import subprocess
import logging
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List

logger = logging.getLogger("anti-gravity-bridge.provenance")

def get_git_commit() -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except Exception:
        return "unknown"

def get_tool_versions() -> Dict[str, str]:
    versions = {}

    # 1. Blender
    blender_exe = os.getenv("BLENDER_PATH", "blender")
    blender_dry_run = os.getenv("BLENDER_DRY_RUN", "true").lower() in ("true", "1", "yes")
    if blender_dry_run:
        versions["blender"] = "mock"
    else:
        try:
            res = subprocess.run(
                [blender_exe, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            lines = res.stdout.splitlines() if res.stdout else []
            first_line = lines[0] if lines else ""
            versions["blender"] = first_line.strip() if first_line else "unknown"
        except Exception:
            versions["blender"] = "mock"

    # 2. Meshroom
    meshroom_exe = os.getenv("MESHROOM_PATH", "meshroom_batch")
    meshroom_dry_run = os.getenv("MESHROOM_DRY_RUN", "true").lower() in ("true", "1", "yes")
    if meshroom_dry_run:
        versions["meshroom"] = "mock"
    else:
        try:
            res = subprocess.run(
                [meshroom_exe, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            lines = res.stdout.splitlines() if res.stdout else []
            first_line = lines[0] if lines else ""
            versions["meshroom"] = first_line.strip() if first_line else "unknown"
        except Exception:
            versions["meshroom"] = "mock"

    # 3. Unity
    versions["unity"] = "mock"

    return versions

def compute_sha256(filepath: str) -> str:
    if not os.path.exists(filepath) or os.path.isdir(filepath):
        return ""
    h = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        logger.error(f"Error computing hash for {filepath}: {e}")
        return ""

def generate_provenance(
    job_id: str,
    command: Dict[str, Any],
    input_files: List[str],
    output_files: List[str]
) -> Dict[str, Any]:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    input_hashes = {}
    for path in input_files:
        full_path = path if os.path.isabs(path) else os.path.join(base_dir, path)
        h = compute_sha256(full_path)
        if h:
            input_hashes[path] = h

    output_hashes = {}
    for path in output_files:
        full_path = path if os.path.isabs(path) else os.path.join(base_dir, path)
        h = compute_sha256(full_path)
        if h:
            output_hashes[path] = h

    py_ver = platform.python_version()
    os_info = f"{platform.system()} {platform.release()}"

    # Import dynamically to prevent circular dependencies
    from orchestrator.resource_manager import get_resource_snapshot

    provenance_data = {
        "job_id": job_id,
        "logical_provenance": {
            "git_commit": get_git_commit(),
            "input_hashes": input_hashes,
            "output_hashes": output_hashes,
            "command_type": command.get("command_type") or command.get("capability_id") or "unknown",
            "command_payload": command.get("payload") or command.get("command_payload") or command,
        },
        "empirical_provenance": {
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "os": os_info,
            "python_version": py_ver,
            "tool_versions": get_tool_versions(),
            "resource_snapshot": get_resource_snapshot(),
            "non_determinism_flags": ["gpu_float_rounding", "thread_scheduling_drift"]
        },
        # Backward compatibility for legacy tests
        "command": command,
        "input_hashes": input_hashes,
        "output_hashes": output_hashes,
        "git_commit": get_git_commit(),
        "python_version": py_ver,
        "os": os_info,
        "tool_versions": get_tool_versions()
    }

    job_dir = os.path.join(base_dir, "artifacts", "jobs", job_id)
    os.makedirs(job_dir, exist_ok=True)
    prov_file = os.path.join(job_dir, "provenance.json")

    try:
        import json
        with open(prov_file, "w", encoding="utf-8") as f:
            json.dump(provenance_data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to persist provenance for job {job_id}: {e}")

    return provenance_data
