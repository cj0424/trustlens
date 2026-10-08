"""TrustLens record: saves every errand and every step to a small database
(data/trustlens.db). All six TrustLens steps read and write this record,
which is what connects them into one system."""

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB_FILE = Path(__file__).resolve().parent.parent / "data" / "trustlens.db"


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Record:
    def __init__(self, path=DB_FILE):
        # check_same_thread=False lets the MCP server's workers share the connection.
        # The lock makes sure only one of them writes at a time.
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        with self.lock:
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS errands ("
                "id TEXT PRIMARY KEY, user_id TEXT, request TEXT, started_at TEXT, status TEXT)"
            )
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS events ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, errand_id TEXT, time TEXT, "
                "step TEXT, kind TEXT, details TEXT)"
            )
            self.conn.commit()

    def start_errand(self, user_id, request):
        """Create a new errand and return its ID."""
        errand_id = uuid.uuid4().hex[:12]
        with self.lock:
            self.conn.execute(
                "INSERT INTO errands VALUES (?, ?, ?, ?, ?)",
                (errand_id, user_id, request, _now(), "running"),
            )
            self.conn.commit()
        return errand_id

    def add_event(self, errand_id, step, kind, details):
        """Save one event. 'step' says which part produced it:
        agent, detect, verify, decide, enforce or learn."""
        with self.lock:
            self.conn.execute(
                "INSERT INTO events (errand_id, time, step, kind, details) VALUES (?, ?, ?, ?, ?)",
                (errand_id, _now(), step, kind, json.dumps(details)),
            )
            self.conn.commit()

    def finish_errand(self, errand_id, status):
        with self.lock:
            self.conn.execute("UPDATE errands SET status = ? WHERE id = ?", (status, errand_id))
            self.conn.commit()

    def errand(self, errand_id):
        with self.lock:
            row = self.conn.execute("SELECT * FROM errands WHERE id = ?", (errand_id,)).fetchone()
        return dict(row) if row else None

    def latest_errand(self):
        with self.lock:
            row = self.conn.execute(
                "SELECT * FROM errands ORDER BY started_at DESC, rowid DESC LIMIT 1"
            ).fetchone()
        return dict(row) if row else None

    def events(self, errand_id):
        with self.lock:
            rows = self.conn.execute(
                "SELECT time, step, kind, details FROM events WHERE errand_id = ? ORDER BY id",
                (errand_id,),
            ).fetchall()
        return [
            {"time": r["time"], "step": r["step"], "kind": r["kind"], "details": json.loads(r["details"])}
            for r in rows
        ]