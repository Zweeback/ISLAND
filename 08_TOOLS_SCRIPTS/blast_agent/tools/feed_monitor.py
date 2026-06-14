import sys
import time
import os
import json
from datetime import datetime, timezone
from pathlib import Path
from island_bus import IslandBus

# Determine the path for the long-term log file
LOG_FILE = Path(__file__).resolve().parents[3] / "06_GATEWAY_LIVEFEED" / "development_feed.jsonl"

def mirror_to_history(event_dict):
    """Writes a copy of the event to the permanent JSONL feed."""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(event_dict, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[Monitor Error] Could not write to JSONL log file: {e}", file=sys.stderr)

def main():
    print(f"--- ISLAND DEVELOPMENT FEED MONITOR ACTIVE ---")
    print(f"Mirroring to: {LOG_FILE}")
    print(f"Listening for events from all AI instances... (Ctrl+C to stop)\n")

    bus = IslandBus()

    try:
        while True:
            events = bus.subscribe("")

            if events:
                for event in events:
                    # Format: [TIMESTAMP] SENDER >> TOPIC: Payload
                    ts = event.get("timestamp", datetime.now(timezone.utc).isoformat())
                    topic = event.get("topic", "unknown")
                    payload = event.get("payload", {})

                    sender = payload.get("agent", payload.get("sender", "system"))
                    if isinstance(sender, str):
                        sender = sender.upper()

                    print(f"[{ts}] {sender} >> {topic}: {payload}")

                    mirror_to_history(event)

                    bus.mark_completed(event["id"])

            time.sleep(1.0)

    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")

if __name__ == "__main__":
    main()
