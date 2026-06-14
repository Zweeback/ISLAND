import sqlite3
import json
import os
from datetime import datetime, timezone
from pathlib import Path

# Define path for DB inside the LiveFeed zone
DB_PATH = str(Path(__file__).resolve().parents[3] / "06_GATEWAY_LIVEFEED" / "island_bus.db")

class IslandBus:
    """
    A high-performance, SQLite-backed event queue for the Zentrale Insel.
    This acts as the 'nervous system' for inter-agent communication (Jules, Codex, Antigravity).
    """
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initializes the database schema if it doesn't exist."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT DEFAULT 'pending'
                )
            ''')
            # Index on topic and status for faster querying
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_topic_status ON events(topic, status)')
            conn.commit()

    def publish(self, topic: str, payload: dict):
        """
        Publishes a new event to the bus.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        payload_json = json.dumps(payload)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO events (timestamp, topic, payload) VALUES (?, ?, ?)',
                (timestamp, topic, payload_json)
            )
            conn.commit()
            print(f"[IslandBus] Published event on topic '{topic}'")

    def subscribe(self, topic_prefix: str, limit: int = 50):
        """
        Retrieves pending events that match the topic prefix.
        E.g., topic_prefix 'system.' will match 'system.init', 'system.resource', etc.
        """
        events = []
        with sqlite3.connect(self.db_path) as conn:
            # We want to return rows as dictionaries
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Using LIKE for prefix matching. E.g., 'system.%'
            like_pattern = f"{topic_prefix}%"
            cursor.execute(
                "SELECT id, timestamp, topic, payload FROM events WHERE status = 'pending' AND topic LIKE ? ORDER BY timestamp ASC LIMIT ?",
                (like_pattern, limit)
            )

            for row in cursor.fetchall():
                events.append({
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "topic": row["topic"],
                    "payload": json.loads(row["payload"])
                })
        return events

    def mark_completed(self, event_id: int):
        """Marks an event as completed so it isn't processed again."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE events SET status = 'completed' WHERE id = ?", (event_id,))
            conn.commit()

if __name__ == "__main__":
    # Test the bus
    bus = IslandBus()
    bus.publish("system.init", {"message": "IslandBus initialized and online.", "agent": "codex"})
    print("Test: Published 'system.init'")

    events = bus.subscribe("system.")
    print(f"Test: Retrieved {len(events)} events matching 'system.'")
    for e in events:
        print(f" - {e['topic']}: {e['payload']}")
        bus.mark_completed(e["id"])
