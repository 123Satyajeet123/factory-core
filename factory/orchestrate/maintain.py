"""The pass that makes receipts move things.

WITHOUT A CALLER, `memory/promote.py` AND `memory/demote.py` ARE DEAD. A resolution that
earned a wider scope stays where it was, and one that stopped working answers forever. Both
existed with no call site, which is the defect this closes.

NOT INSIDE A RUN. A run collects receipts; what they add up to is a separate pass, because
promotion should read every receipt an entry has rather than the last one -- and because a
run promoting its own resolutions mid-flight would be marking its own paper.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from factory.core.memory import Kind, Tier
from factory.memory.confidence import bound


class Moved(BaseModel):
    """What a sweep changed, so a quiet pass is distinguishable from a stuck one."""

    elevated: list[str] = Field(default_factory=list)
    demoted: list[str] = Field(default_factory=list)
    left: int = 0

    def said(self) -> str:
        return (f"{len(self.elevated)} earned a wider scope, "
                f"{len(self.demoted)} fell, {self.left} unchanged")


def sweep(memory: Any, *, earned: float = 0.75,
          kinds: tuple[Kind, ...] = (Kind.TARGET,)) -> Moved:
    """Elevate what the receipts earned, drop what they refuted, leave the rest."""
    moved = Moved()
    for entry in memory.every(kinds):
        standing = bound(entry.confidence)

        if (standing >= earned and entry.tier is not Tier.MAIN
                and memory.elevate(entry, earned=earned) is not None):
            moved.elevated.append(entry.key)
            continue

        if (entry.confidence.refuted and standing < earned
                and memory.demote(entry, earned=earned) is not None):
            moved.demoted.append(entry.key)
            continue

        moved.left += 1
    return moved
