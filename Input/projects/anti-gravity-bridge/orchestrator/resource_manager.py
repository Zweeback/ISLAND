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

    # Define minimal hardware requirements
    # Target Meshroom: requires 6GB VRAM (or RAM fallback if dry run)
    if target == "meshroom":
        required_vram = 6000
        if vram < required_vram and not os.environ.get("BLENDER_DRY_RUN", "false").lower() in ("true", "1"):
            # Check if we can fallback to CPU memory or if it is a hard fail
            return False, f"insufficient_vram: Meshroom requires {required_vram}MB free VRAM (free: {vram}MB)"
        if ram < 4000:
            return False, f"insufficient_ram: Meshroom requires 4000MB free RAM (free: {ram}MB)"

    # Target Blender: requires 4GB VRAM
    elif target == "blender":
        required_vram = 4000
        # If GPU is needed for Cycles rendering
        if "render_scene" in command_type:
            if vram < required_vram and not os.environ.get("BLENDER_DRY_RUN", "false").lower() in ("true", "1"):
                return False, f"insufficient_vram: Blender Cycles render requires {required_vram}MB free VRAM (free: {vram}MB)"
        if ram < 2000:
            return False, f"insufficient_ram: Blender requires 2000MB free RAM (free: {ram}MB)"

    return True, "resources_available"

async def unload_ollama_model(model_name: str = "gemma4") -> bool:
    """
    Unloads the active Ollama model weights from GPU VRAM to free resources.
    Uses the keep_alive: 0 option.
    """
    import httpx
    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    url = f"{host}/api/generate"
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            res = await client.post(url, json={"model": model_name, "prompt": "", "keep_alive": 0})
            if res.status_code == 200:
                logger.info(f"Successfully unloaded Ollama model: {model_name}")
                return True
    except Exception as e:
        logger.warning(f"Could not connect to Ollama to unload model {model_name}: {e}")
    return False
