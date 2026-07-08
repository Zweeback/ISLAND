import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Set, Any

logger = logging.getLogger("anti-gravity-bridge.state_machine")

ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
    "queued": {"validating", "cancelled"},
    "accepted": {"validating", "cancelled"},
    "validating": {"ready", "failed", "cancelled"},
    "ready": {"running", "cancelled"},
    "running": {"succeeded", "failed", "cancelled"},
    "failed": {"retrying", "cancelled"},
    "retrying": {"running", "cancelled"},
    "succeeded": set(),
    "cancelled": set()
}

class JobStateMachine:
    """
    State machine enforcing strict transition rules for background jobs.
    Persists status outputs to artifacts/jobs/{job_id}/job_state.json.
    """

    def __init__(self, job_id: str, initial_state: str = "queued"):
        self.job_id = job_id
        self.state = initial_state
        self.history: List[Dict[str, Any]] = []

        # Setup paths
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.job_dir = os.path.join(base_dir, "artifacts", "jobs", job_id)
        os.makedirs(self.job_dir, exist_ok=True)
        self.state_file = os.path.join(self.job_dir, "job_state.json")

        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                    self.state = data.get("current_state", initial_state)
                    self.history = data.get("history", [])
            except Exception:
                self._record_transition(initial_state)
        else:
            self._record_transition(initial_state)

    def transition_to(self, new_state: str, reason: str = None):
        """
        Guards transitions and writes new state configuration to disk.
        """
        if new_state not in ALLOWED_TRANSITIONS:
            raise ValueError(f"Invalid state: {new_state}")

        allowed = ALLOWED_TRANSITIONS.get(self.state, set())
        if new_state not in allowed:
            raise ValueError(f"Illegal state transition from '{self.state}' to '{new_state}'")

        old_state = self.state
        self.state = new_state
        self._record_transition(new_state, reason)

        logger.info(f"Job {self.job_id} transitioned: {old_state} -> {new_state} (Reason: {reason})")

    def _record_transition(self, state: str, reason: str = None):
        entry = {
            "state": state,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "reason": reason
        }
        self.history.append(entry)
        self._persist()

    def _persist(self):
        existing = {}
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                pass

        existing["job_id"] = self.job_id
        existing["current_state"] = self.state
        existing["state"] = self.state  # Align with v2 Pydantic schema
        existing["history"] = self.history
        existing["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
