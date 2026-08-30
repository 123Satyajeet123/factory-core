"""The MEMORY machine: resolve, write, elevate, demote.

Three tiers with inheritance down and elevation up. Nothing is copied between them: a
narrower entry shadows a wider one, and resolution walks EXECUTION, WORKFLOW, MAIN and
takes the first hit.

ELEVATION IS EARNED, ON RECEIPTS AND NOTHING ELSE. A witness confirming or refuting is the
only evidence admitted -- never a model's report of how sure it was, which is the answerer
marking its own paper.

DEMOTION IS WHY THE OTHER TWO ARE SAFE. Without it memory only accumulates, and an entry
that stopped being true stays authoritative forever.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from factory.core.memory import Confidence, Entry, Kind, Tier
from factory.memory import scope as scoping
from factory.memory.confidence import bound
from factory.store.db import open_at

#: The bound an entry must clear to earn a wider scope. One threshold, one meaning: how
#: sure we insist on being. `evals/memory` moves it and reports what it promotes.
EARNED = 0.75


def _row(row: sqlite3.Row) -> Entry:
    return Entry(kind=Kind(row["kind"]), tier=Tier(row["tier"]), scope=row["scope"],
                 key=row["key"], value=json.loads(row["value"]),
                 confidence=Confidence(confirmed=row["confirmed"], refuted=row["refuted"]),
                 at=datetime.fromisoformat(row["at"]))


class Memory:
    """What is known, at what scope, on what evidence."""

    def __init__(self, at: Path | str = ":memory:") -> None:
        self._db = open_at(at)

    def remember(self, kind: Kind, key: str, value: Any, *,
                 tier: Tier = Tier.MAIN, scope: str = "") -> Entry:
        """Write it, or replace what was there. Confidence starts empty."""
        entry = Entry(kind=kind, tier=tier, scope=scope, key=key, value=value)
        self._db.execute(
            "INSERT INTO entry (kind, tier, scope, key, value, at) VALUES (?,?,?,?,?,?) "
            "ON CONFLICT (kind, tier, scope, key) DO UPDATE SET value=excluded.value, "
            "at=excluded.at",
            (kind, tier, scope, key, json.dumps(value), entry.at.isoformat()))
        return entry

    def recall(self, kind: Kind, key: str, *,
               run: str = "", workflow: str = "") -> Entry | None:
        """Narrowest first. The first hit wins, and that is the inheritance."""
        for tier, scope in scoping.chain(run, workflow):
            got = self._db.execute(
                "SELECT * FROM entry WHERE kind=? AND tier=? AND scope=? AND key=?",
                (kind, tier, scope, key)).fetchone()
            if got:
                return _row(got)
        return None

    def witnessed(self, entry: Entry, confirmed: bool) -> Entry:
        """One receipt. The only thing that moves an entry's standing."""
        #: Two statements rather than an interpolated column name: nothing user-supplied
        #: ever reaches SQL text here.
        change = ("UPDATE entry SET confirmed = confirmed + 1 " if confirmed
                  else "UPDATE entry SET refuted = refuted + 1 ")
        self._db.execute(
            change + "WHERE kind=? AND tier=? AND scope=? AND key=?",
            (entry.kind, entry.tier, entry.scope, entry.key))
        again = self.at(entry.kind, entry.key, entry.tier, entry.scope)
        assert again is not None
        return again

    def at(self, kind: Kind, key: str, tier: Tier, scope: str = "") -> Entry | None:
        """One exact entry, without walking the chain."""
        got = self._db.execute(
            "SELECT * FROM entry WHERE kind=? AND tier=? AND scope=? AND key=?",
            (kind, tier, scope, key)).fetchone()
        return _row(got) if got else None

    def elevate(self, entry: Entry, *, earned: float = EARNED) -> Entry | None:
        """Move it a tier wider if its receipts say so. Returns where it went, or None."""
        wider = scoping.wider(entry.tier)
        if wider is None or bound(entry.confidence) < earned:
            return None
        #: A wider scope is a smaller scope string, not a bigger one: WORKFLOW keeps the
        #: workflow, MAIN keeps nothing.
        scope = "" if wider is Tier.MAIN else entry.scope
        self.remember(entry.kind, entry.key, entry.value, tier=wider, scope=scope)
        self.forget(entry)
        return self.at(entry.kind, entry.key, wider, scope)

    def demote(self, entry: Entry, *, earned: float = EARNED) -> Entry | None:
        """A refuted entry falls a tier, or goes. Returns where it went, or None."""
        if bound(entry.confidence) >= earned:
            return None
        self.forget(entry)
        narrower = scoping.narrower(entry.tier)
        if narrower is None:
            return None
        self.remember(entry.kind, entry.key, entry.value, tier=narrower, scope=entry.scope)
        return self.at(entry.kind, entry.key, narrower, entry.scope)

    def forget(self, entry: Entry) -> None:
        self._db.execute(
            "DELETE FROM entry WHERE kind=? AND tier=? AND scope=? AND key=?",
            (entry.kind, entry.tier, entry.scope, entry.key))


def _self_check() -> None:
    """Inheritance, earned elevation, demotion. No browser and no store on disk.

        uv run python -m factory.memory.driver
    """
    memory = Memory()

    memory.remember(Kind.TARGET, "save", "wide", tier=Tier.MAIN)
    memory.remember(Kind.TARGET, "save", "narrow", tier=Tier.EXECUTION, scope="run-1")
    assert memory.recall(Kind.TARGET, "save", run="run-1").value == "narrow", "narrow shadows"
    assert memory.recall(Kind.TARGET, "save", run="run-2").value == "wide", "and only there"
    assert memory.recall(Kind.TARGET, "save").value == "wide", "MAIN answers with no scope"

    entry = memory.at(Kind.TARGET, "save", Tier.EXECUTION, "run-1")
    assert memory.elevate(entry) is None, "no receipts, no promotion"
    for _ in range(3):
        entry = memory.witnessed(entry, True)
    assert memory.elevate(entry) is None, "three in a row is 0.44, and does not clear 0.75"
    for _ in range(9):
        entry = memory.witnessed(entry, True)
    moved = memory.elevate(entry)
    assert moved and moved.tier is Tier.WORKFLOW, f"twelve is 0.76, and does: {moved}"
    assert memory.at(Kind.TARGET, "save", Tier.EXECUTION, "run-1") is None, "moved, not copied"

    for _ in range(9):
        moved = memory.witnessed(moved, False)
    fell = memory.demote(moved)
    assert fell and fell.tier is Tier.EXECUTION, f"refutations drop it back: {fell}"
    print("memory: inheritance, earned elevation, demotion on refutation")


if __name__ == "__main__":
    _self_check()
