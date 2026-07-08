from __future__ import annotations

import json
import os
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("anti-gravity-bridge.deferred_queue")

BASE_DIR = Path(__file__).resolve().parent.parent
DEFERRED_DIR = BASE_DIR / "artifacts" / "deferred"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _entry_path(job_id: str) -> Path:
    DEFERRED_DIR.mkdir(parents=True, exist_ok=True)
    return DEFERRED_DIR / f"{job_id}.json"


def max_retries() -> int:
    return int(os.getenv("DEFERRED_MAX_RETRIES", "5"))


def backoff_base_sec() -> float:
    return float(os.getenv("DEFERRED_BACKOFF_BASE_SEC", "10"))


def compute_next_retry_at(retry_count: int) -> str:
    delay = backoff_base_sec() * (1.5 ** max(0, retry_count - 1))
    when = datetime.now(timezone.utc) + timedelta(seconds=delay)
    return when.isoformat().replace("+00:00", "Z")


def enqueue_deferred_job(job_id: str, command: Dict[str, Any], reason: str) -> Dict[str, Any]:
    entry = {
        "job_id": job_id,
        "command": command,
        "reason": reason,
        "retry_count": 0,
        "max_retries": max_retries(),
        "next_retry_at": _utcnow(),
        "created_at": _utcnow(),
        "dispatching": False,
    }
    _entry_path(job_id).write_text(json.dumps(entry, indent=2), encoding="utf-8")
    logger.info("Enqueued deferred job %s: %s", job_id, reason)
    return entry


def load_deferred_entry(job_id: str) -> Optional[Dict[str, Any]]:
    path = _entry_path(job_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.error("Failed to read deferred entry %s: %s", job_id, exc)
        return None


def save_deferred_entry(entry: Dict[str, Any]) -> None:
    job_id = entry["job_id"]
    _entry_path(job_id).write_text(json.dumps(entry, indent=2), encoding="utf-8")


def remove_deferred_entry(job_id: str) -> None:
    path = _entry_path(job_id)
    if path.exists():
        path.unlink()


def list_deferred_entries() -> List[Dict[str, Any]]:
    if not DEFERRED_DIR.exists():
        return []
    entries: List[Dict[str, Any]] = []
    for path in DEFERRED_DIR.glob("*.json"):
        try:
            entries.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return entries


def load_due_deferred_jobs() -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc)
    due: List[Dict[str, Any]] = []
    for entry in list_deferred_entries():
        if entry.get("dispatching"):
            continue
        raw = entry.get("next_retry_at")
        if not raw:
            due.append(entry)
            continue
        try:
            ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if ts <= now:
                due.append(entry)
        except Exception:
            due.append(entry)
    return due


def queue_depth() -> int:
    return len(list_deferred_entries())