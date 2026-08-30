from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from factory.core.memory import Kind, Tier
from factory.orchestrate import lease as leases
from factory.orchestrate.schedule import Cadence, owed


class Owed(BaseModel):
    cadence: Cadence
    runs: int
    held_by: str = ""

    @property
    def startable(self) -> bool:
        return self.runs > 0 and self.cadence.allowed and not self.held_by


def cadences(memory: Any) -> list[Cadence]:
    return [Cadence.model_validate(entry.value)
            for entry in memory.every((Kind.CADENCE,))]


def set_cadence(memory: Any, cadence: Cadence) -> Cadence:
    memory.remember(Kind.CADENCE, cadence.workflow, cadence.model_dump(mode="json"),
                    tier=Tier.WORKFLOW, scope=cadence.workflow)
    return cadence


def waiting(memory: Any, db: sqlite3.Connection,
            now: datetime | None = None) -> list[Owed]:
    now = now or datetime.now(UTC)
    standing = []
    for cadence in cadences(memory):
        held = leases.holder(db, cadence.workflow, now)
        standing.append(Owed(cadence=cadence, runs=owed(cadence, now),
                             held_by=held.holder if held else ""))
    return sorted(standing, key=lambda o: (-o.runs, o.cadence.workflow))


def claim(memory: Any, db: sqlite3.Connection, workflow: str,
          now: datetime | None = None) -> leases.Held | None:
    now = now or datetime.now(UTC)
    for cadence in cadences(memory):
        if cadence.workflow != workflow:
            continue
        if not cadence.allowed or owed(cadence, now) < 1:
            return None
        return leases.take(db, workflow, now=now)
    return None


def ran(memory: Any, workflow: str, at: datetime | None = None) -> Cadence | None:
    for cadence in cadences(memory):
        if cadence.workflow == workflow:
            return set_cadence(memory, cadence.model_copy(
                update={"last": at or datetime.now(UTC)}))
    return None


def _self_check() -> None:
    """uv run python -m factory.orchestrate.driver"""
    from datetime import timedelta

    from factory.memory.driver import Memory
    from factory.store.db import open_at

    memory, db = Memory(), open_at(":memory:")
    monday = datetime(2026, 8, 31, 9, 30, tzinfo=UTC)

    set_cadence(memory, Cadence(workflow="outreach", crontab="0 9 * * *",
                                last=monday.replace(hour=9), allowed=True))
    set_cadence(memory, Cadence(workflow="unallowed", crontab="0 9 * * *",
                                last=monday.replace(hour=9)))

    assert [o.runs for o in waiting(memory, db, monday)] == [0, 0], "nothing owed yet"
    assert claim(memory, db, "outreach", monday) is None, "not due, not claimable"

    tuesday = monday + timedelta(days=1)
    standing = {o.cadence.workflow: o for o in waiting(memory, db, tuesday)}
    assert standing["outreach"].runs == 1 and standing["outreach"].startable
    assert standing["unallowed"].runs == 1, "owed"
    assert not standing["unallowed"].startable, "and still not startable"
    assert claim(memory, db, "unallowed", tuesday) is None, "nobody allowed it"

    held = claim(memory, db, "outreach", tuesday)
    assert held, "due and allowed is claimable"
    assert claim(memory, db, "outreach", tuesday) is None, "and only once"
    assert waiting(memory, db, tuesday)[0].held_by == held.holder

    ran(memory, "outreach", tuesday)
    leases.drop(db, held)
    assert [o.runs for o in waiting(memory, db, tuesday)
            if o.cadence.workflow == "outreach"] == [0], "a run clears what was owed"
    print("orchestrate: owed is counted for every workflow, startable only for one a "
          "person allowed and nobody holds, and claiming is exclusive")


if __name__ == "__main__":
    _self_check()
