import os
import subprocess
import shutil
import logging
import psutil
from typing import Dict, Any, Tuple

logger = logging.getLogger("anti-gravity-bridge.resource_manager")

def get_free_vram() -> int:
    """
    Returns free VRAM in MB.
    Uses nvidia-smi if available. Support environment variable override for testing.
    """
    # Environment variable override for testing
    if "MOCK_VRAM_FREE_MB" in os.environ:
        try:
            return int(os.environ["MOCK_VRAM_FREE_MB"])
        except ValueError:
            pass

    nvismi = shutil.which("nvidia-smi")
    if not nvismi:
        return 0
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
            check=True
        )
        lines = res.stdout.strip().splitlines()
        if lines:
            return int(lines[0].strip())
    except Exception as e:
        logger.debug(f"nvidia-smi query failed: {e}")
    return 0

def get_resource_snapshot() -> Dict[str, Any]:
    """
    Returns a snapshot of the current system resource telemetry.
    """
    # Environment override for virtual memory for testing
    ram_avail = psutil.virtual_memory().available
    if "MOCK_RAM_FREE_MB" in os.environ:
        try:
            ram_avail = int(os.environ["MOCK_RAM_FREE_MB"]) * 1024 * 1024
        except ValueError:
            pass

    return {
        "cpu_percent": psutil.cpu_percent(),
        "ram_available_mb": ram_avail // (1024 * 1024),
        "ram_total_mb": psutil.virtual_memory().total // (1024 * 1024),
        "vram_free_mb": get_free_vram(),
    }

def admit_job(target: str, command_type: str) -> Tuple[bool, str]:
    """
    Evaluates if system has enough VRAM/RAM to execute the specified target job.
    Returns: (admitted: bool, reason_or_error: str)
    """
    snapshot = get_resource_snapshot()
    vram = snapshot["vram_free_mb"]
    ram = snapshot["ram_available_mb"]

    # Define minimal hardware requirements (always enforced; cmd.dry_run bypasses guard in main)
    if target == "meshroom":
        required_vram = 6000
        if vram < required_vram:
            return False, f"insufficient_vram: Meshroom requires {required_vram}MB free VRAM (free: {vram}MB)"
        if ram < 4000:
            return False, f"insufficient_ram: Meshroom requires 4000MB free RAM (free: {ram}MB)"

    elif target == "blender":
        required_vram = 4000
        if "render_scene" in command_type:
            if vram < required_vram:
                return False, (
                    f"insufficient_vram: Blender Cycles render requires "
                    f"{required_vram}MB free VRAM (free: {vram}MB)"
                )
        if ram < 2000:
            return False, f"insufficient_ram: Blender requires 2000MB free RAM (free: {ram}MB)"

    return True, "resources_available"

def is_ollama_unload_allowed() -> bool:
    """Ollama unload requires explicit opt-in via ALLOW_OLLAMA_UNLOAD=true."""
    return os.environ.get("ALLOW_OLLAMA_UNLOAD", "").lower() in ("true", "1", "yes")


def _apply_mock_vram_unload(freed_mb: int) -> None:
    current = int(os.environ.get("MOCK_VRAM_FREE_MB", "0"))
    os.environ["MOCK_VRAM_FREE_MB"] = str(current + freed_mb)


async def unload_ollama_model(model_name: str = "gemma4") -> bool:
    """
    Unloads Ollama model weights from GPU VRAM. Requires ALLOW_OLLAMA_UNLOAD=true.
    MOCK_OLLAMA_UNLOAD enables deterministic tests (also requires the flag).
    """
    if not is_ollama_unload_allowed():
        logger.info("Ollama unload skipped: ALLOW_OLLAMA_UNLOAD is not enabled")
        return False

    if os.environ.get("MOCK_OLLAMA_UNLOAD", "").lower() in ("true", "1", "yes"):
        freed_mb = int(os.environ.get("MOCK_VRAM_FREED_MB", "5000"))
        _apply_mock_vram_unload(freed_mb)
        logger.info(
            "Mock unloaded Ollama model %s, freed %sMB VRAM", model_name, freed_mb
        )
        return True

    import httpx
    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    url = f"{host}/api/generate"
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            res = await client.post(
                url, json={"model": model_name, "prompt": "", "keep_alive": 0}
            )
            if res.status_code == 200:
                logger.info("Successfully unloaded Ollama model: %s", model_name)
                return True
    except Exception as e:
        logger.warning(
            "Could not connect to Ollama to unload model %s: %s", model_name, e
        )
    return False


async def admit_job_with_recovery(
    target: str,
    command_type: str,
    model_name: str = "gemma4",
) -> Tuple[bool, str, bool]:
    """
    Admission with one VRAM recovery attempt via Ollama unload.
    Returns: (admitted, reason, ollama_unloaded)
    """
    admitted, reason = admit_job(target, command_type)
    if admitted:
        return True, reason, False
    if "insufficient_vram" not in reason:
        return False, reason, False

    if not is_ollama_unload_allowed():
        logger.info(
            "VRAM low, but ALLOW_OLLAMA_UNLOAD is not enabled. Skipping VRAM recovery."
        )
        return False, reason, False

    logger.info("VRAM low. Attempting to unload Ollama model '%s'...", model_name)
    unloaded = await unload_ollama_model(model_name)
    if not unloaded:
        return False, reason, False

    admitted, reason = admit_job(target, command_type)
    return admitted, reason, True
