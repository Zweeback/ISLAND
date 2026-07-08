from __future__ import annotations

import asyncio
import logging
import os
from typing import Awaitable, Callable, Set

from orchestrator.deferred_queue import (
    compute_next_retry_at,
    load_due_deferred_jobs,
    release_deferred_claim,
    remove_deferred_entry,
    save_deferred_entry,
    try_claim_deferred_job,
)

logger = logging.getLogger("anti-gravity-bridge.retry_scheduler")

_dispatching: Set[str] = set()


def retry_interval_sec() -> float:
    return float(os.getenv("DEFERRED_RETRY_INTERVAL_SEC", "30"))


def is_dispatching(job_id: str) -> bool:
    return job_id in _dispatching


async def process_deferred_once(
    retry_fn: Callable[[dict], Awaitable[None]],
) -> int:
    entries = load_due_deferred_jobs()
    processed = 0
    for entry in entries:
        job_id = entry.get("job_id")
        if not job_id or job_id in _dispatching:
            continue
        claimed = try_claim_deferred_job(job_id)
        if not claimed:
            continue
        _dispatching.add(job_id)
        try:
            await retry_fn(claimed)
            processed += 1
        finally:
            _dispatching.discard(job_id)
            release_deferred_claim(job_id)
    return processed


async def retry_scheduler_loop(
    retry_fn: Callable[[dict], Awaitable[None]],
) -> None:
    interval = retry_interval_sec()
    while True:
        try:
            await process_deferred_once(retry_fn)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("Deferred retry scheduler error: %s", exc)
        await asyncio.sleep(interval)


def mark_retry_scheduled(entry: dict, reason: str) -> dict:
    from orchestrator.deferred_queue import release_deferred_claim

    job_id = entry["job_id"]
    entry["retry_count"] = int(entry.get("retry_count", 0)) + 1
    entry["reason"] = reason
    entry["next_retry_at"] = compute_next_retry_at(entry["retry_count"])
    entry["dispatching"] = False
    entry.pop("claimed_at", None)
    entry.pop("claimed_by_pid", None)
    save_deferred_entry(entry)
    release_deferred_claim(job_id)
    return entry


def mark_retry_exhausted(entry: dict) -> None:
    remove_deferred_entry(entry["job_id"])