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
    caused     INTEGER NOT NULL DEFAULT 0,
    at         TEXT NOT NULL,
    until      TEXT,
    PRIMARY KEY (kind, tier, scope, key)
);

CREATE TABLE IF NOT EXISTS lease (
    workflow   TEXT PRIMARY KEY,
    holder     TEXT NOT NULL,
    taken_at   TEXT NOT NULL,
    until      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS question (
    kind        TEXT NOT NULL,
    about       TEXT NOT NULL,
    because     TEXT NOT NULL DEFAULT '',
    candidates  TEXT NOT NULL DEFAULT '',
    answer      TEXT,
    asked_at    TEXT NOT NULL,
    answered_at TEXT,
    PRIMARY KEY (kind, about)
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
    #: A column added after a store existed. `CREATE TABLE IF NOT EXISTS` will not add one,
    #: and an older file would otherwise fail on first read rather than on migration.
    held = {row["name"] for row in db.execute("PRAGMA table_info(entry)")}
    if "until" not in held:
        db.execute("ALTER TABLE entry ADD COLUMN until TEXT")
    if "caused" not in held:
        db.execute("ALTER TABLE entry ADD COLUMN caused INTEGER NOT NULL DEFAULT 0")
    return db
