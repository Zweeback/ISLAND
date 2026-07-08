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

SENSITIVE_KEY_FRAGMENTS = ("api_key", "token", "secret", "password", "sk-", "llm_raw_text")
REDACTED = "[REDACTED]"


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


def claim_stale_sec() -> float:
    return float(os.getenv("DEFERRED_CLAIM_STALE_SEC", "300"))


def _is_sensitive_key(key: str) -> bool:
    lower = key.lower()
    return any(fragment in lower for fragment in SENSITIVE_KEY_FRAGMENTS)


def sanitize_command_for_deferred(command: Dict[str, Any]) -> Dict[str, Any]:
    def _sanitize(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: REDACTED if _is_sensitive_key(key) else _sanitize(nested)
                for key, nested in value.items()
            }
        if isinstance(value, list):
            return [_sanitize(item) for item in value]
        return value

    return _sanitize(command)


def _claim_lock_path(job_id: str) -> Path:
    return _entry_path(job_id).with_suffix(".claim")


def _is_stale_claim(entry: Dict[str, Any], now: Optional[datetime] = None) -> bool:
    if not entry.get("dispatching"):
        return False
    now = now or datetime.now(timezone.utc)
    raw = entry.get("claimed_at")
    if not raw:
        return True
    try:
        claimed_at = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return (now - claimed_at).total_seconds() > claim_stale_sec()
    except Exception:
        return True


def try_claim_deferred_job(job_id: str) -> Optional[Dict[str, Any]]:
    path = _entry_path(job_id)
    if not path.exists():
        return None

    entry = load_deferred_entry(job_id)
    if not entry:
        return None

    now = datetime.now(timezone.utc)
    lock_path = _claim_lock_path(job_id)

    if entry.get("dispatching") and not _is_stale_claim(entry, now):
        return None

    if _is_stale_claim(entry, now):
        entry["dispatching"] = False
        entry.pop("claimed_at", None)
        entry.pop("claimed_by_pid", None)
        lock_path.unlink(missing_ok=True)

    if lock_path.exists():
        try:
            age = (
                now - datetime.fromtimestamp(lock_path.stat().st_mtime, tz=timezone.utc)
            ).total_seconds()
            if age <= claim_stale_sec():
                return None
            lock_path.unlink(missing_ok=True)
        except Exception:
            return None

    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        try:
            os.write(fd, str(os.getpid()).encode("ascii"))
        finally:
            os.close(fd)
    except FileExistsError:
        return None

    entry["dispatching"] = True
    entry["claimed_at"] = _utcnow()
    entry["claimed_by_pid"] = os.getpid()
    save_deferred_entry(entry)
    return entry


def release_deferred_claim(job_id: str) -> None:
    entry = load_deferred_entry(job_id)
    if entry:
        entry["dispatching"] = False
        entry.pop("claimed_at", None)
        entry.pop("claimed_by_pid", None)
        save_deferred_entry(entry)
    _claim_lock_path(job_id).unlink(missing_ok=True)


def enqueue_deferred_job(job_id: str, command: Dict[str, Any], reason: str) -> Dict[str, Any]:
    entry = {
        "job_id": job_id,
        "command": sanitize_command_for_deferred(command),
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
        if entry.get("dispatching") and not _is_stale_claim(entry, now):
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