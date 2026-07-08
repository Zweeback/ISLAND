import os
import json
import threading
from datetime import datetime, timezone
from typing import Dict, Any

class EventLogger:
    def __init__(self, log_file: str = None):
        if log_file is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_file = os.path.join(base_dir, "artifacts", "events", "events.jsonl")
        self.log_file = log_file
        self.lock = threading.Lock()
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

    def log_event(self, event_type: str, data: Dict[str, Any]):
        event = {
            "event": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "data": data
        }
        with self.lock:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event) + "\n")
            except Exception as e:
                import logging
                logging.getLogger("anti-gravity-bridge.event_logger").error(
                    f"Failed to write event {event_type} to log: {e}"
                )

logger_instance = EventLogger()

def log_event(event_type: str, data: Dict[str, Any]):
    logger_instance.log_event(event_type, data)
