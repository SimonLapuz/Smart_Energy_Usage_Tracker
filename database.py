"""
database.py — SQLite setup and connection helper for Smart Energy Tracker

The DB file is created as  energy.db  in the same directory as this script.
Call init_db() once at startup (done automatically by app.py).
Call get_db()  anywhere you need a connection.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "energy.db")

# ── Schema ────────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    date    TEXT    NOT NULL,           -- ISO 8601, e.g. "2025-04-15"
    type    TEXT    NOT NULL CHECK(type IN ('electricity', 'water')),
    amount  REAL    NOT NULL CHECK(amount > 0),
    note    TEXT    NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_entries_date ON entries(date);
CREATE INDEX IF NOT EXISTS idx_entries_type ON entries(type);
"""

# ── Public helpers ─────────────────────────────────────────────────────────────

def get_db() -> sqlite3.Connection:
    """
    Return a sqlite3 connection with row_factory set so that rows behave
    like dicts (access columns by name: row["date"]).
    A new connection is created each call — fine for a single-threaded dev
    server; swap for a connection pool (e.g. SQLAlchemy) in production.
    """
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")   # safer concurrent reads
    con.execute("PRAGMA foreign_keys=ON")
    return con


def init_db() -> None:
    """Create tables and indexes if they don't already exist."""
    con = get_db()
    con.executescript(SCHEMA)
    con.commit()
    con.close()
    print(f"📂  Database ready at: {DB_PATH}")


# ── Optional CLI seed ─────────────────────────────────────────────────────────

def seed_sample_data() -> None:
    """
    Populate the DB with 30 days of sample data — useful for testing.
    Run directly:  python database.py
    """
    from datetime import date, timedelta
    import random

    con = get_db()
    today = date.today()

    # Clear existing data first
    con.execute("DELETE FROM entries")

    rows = []
    for i in range(29, -1, -1):
        ds = (today - timedelta(days=i)).isoformat()
        rows.append((ds, "electricity", round(8 + random.random() * 8,  1), ""))
        rows.append((ds, "water",       round(80 + random.random() * 120, 0), ""))

    con.executemany(
        "INSERT INTO entries (date, type, amount, note) VALUES (?,?,?,?)",
        rows
    )
    con.commit()
    con.close()
    print(f"✅  Seeded {len(rows)} sample entries into {DB_PATH}")


if __name__ == "__main__":
    init_db()
    seed_sample_data()
