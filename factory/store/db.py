"""One database. Machines hold no state a restart would lose.

The connection, the schema and the one place a transaction is opened.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS entry (
    kind       TEXT NOT NULL,
    tier       TEXT NOT NULL,
    scope      TEXT NOT NULL DEFAULT '',
    key        TEXT NOT NULL,
    value      TEXT NOT NULL,
    confirmed  INTEGER NOT NULL DEFAULT 0,
    refuted    INTEGER NOT NULL DEFAULT 0,
    at         TEXT NOT NULL,
    PRIMARY KEY (kind, tier, scope, key)
);
"""


def open_at(path: Path | str) -> sqlite3.Connection:
    """A connection with the schema applied. Idempotent."""
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript(SCHEMA)
    return db
