from __future__ import annotations

import os
import socket
import sqlite3
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel

HOLD = timedelta(minutes=15)


class Held(BaseModel):
    workflow: str
    holder: str
    taken_at: datetime
    until: datetime

    def good(self, now: datetime | None = None) -> bool:
        return (now or datetime.now(UTC)) < self.until


def me() -> str:
    return f"{socket.gethostname()}:{os.getpid()}"


def _row(row: sqlite3.Row) -> Held:
    return Held(workflow=row["workflow"], holder=row["holder"],
                taken_at=datetime.fromisoformat(row["taken_at"]),
                until=datetime.fromisoformat(row["until"]))


def holder(db: sqlite3.Connection, workflow: str,
           now: datetime | None = None) -> Held | None:
    got = db.execute("SELECT * FROM lease WHERE workflow=?", (workflow,)).fetchone()
    if got is None:
        return None
    held = _row(got)
    return held if held.good(now) else None


def take(db: sqlite3.Connection, workflow: str, *, holder_id: str = "",
         hold: timedelta = HOLD, now: datetime | None = None) -> Held | None:
    now = now or datetime.now(UTC)
    standing = holder(db, workflow, now)
    if standing is not None:
        return None
    taken = Held(workflow=workflow, holder=holder_id or me(), taken_at=now,
                 until=now + hold)
    db.execute(
        "INSERT INTO lease (workflow, holder, taken_at, until) VALUES (?,?,?,?) "
        "ON CONFLICT (workflow) DO UPDATE SET holder=excluded.holder, "
        "taken_at=excluded.taken_at, until=excluded.until",
        (taken.workflow, taken.holder, taken.taken_at.isoformat(),
         taken.until.isoformat()))
    return taken


def extend(db: sqlite3.Connection, held: Held, *, hold: timedelta = HOLD,
           now: datetime | None = None) -> Held | None:
    now = now or datetime.now(UTC)
    standing = holder(db, held.workflow, now)
    if standing is None or standing.holder != held.holder:
        return None
    longer = standing.model_copy(update={"until": now + hold})
    db.execute("UPDATE lease SET until=? WHERE workflow=? AND holder=?",
               (longer.until.isoformat(), longer.workflow, longer.holder))
    return longer


def drop(db: sqlite3.Connection, held: Held) -> None:
    db.execute("DELETE FROM lease WHERE workflow=? AND holder=?",
               (held.workflow, held.holder))


def _self_check() -> None:
    """uv run python -m factory.orchestrate.lease"""
    from factory.store.db import open_at

    db = open_at(":memory:")
    now = datetime(2026, 8, 30, 9, 0, tzinfo=UTC)

    mine = take(db, "outreach", holder_id="a", now=now)
    assert mine and mine.holder == "a"
    assert take(db, "outreach", holder_id="b", now=now) is None, "one runner at a time"
    assert take(db, "other", holder_id="b", now=now), "a different workflow is free"

    later = now + HOLD + timedelta(seconds=1)
    assert holder(db, "outreach", later) is None, "a dead runner lets go"
    assert take(db, "outreach", holder_id="b", now=later), "and somebody else may take it"

    theirs = holder(db, "outreach", later)
    assert extend(db, mine, now=later) is None, "the old holder cannot extend"
    assert extend(db, theirs, now=later), "the current one can"
    assert holder(db, "outreach", later + HOLD - timedelta(seconds=1)) is not None

    drop(db, theirs)
    assert holder(db, "outreach", later) is None, "released"
    assert take(db, "outreach", holder_id="c", now=later), "and free again immediately"
    print("lease: exclusive, expiring, extendable only by its holder, released on drop")


if __name__ == "__main__":
    _self_check()
