"""What could not be witnessed, and what shape of surface defeated it.

THE OUTGOING EDGE `unverifiable` DOES NOT OTHERWISE HAVE. It moves neither side of
`core/memory.Confidence`, so an act nobody could check is invisible to promotion -- which
makes it the ceiling on promotion, and promotion is the ceiling on cheapness. A number
nothing consumes is a number nobody acts on, so this one names the reader worth building.

THE SHAPE IS DERIVED FROM THE EVIDENCE, NEVER FROM THE DESTINATION. Content types the step
actually carried, and the fields no reader could address. A tally keyed by host would tell
you where you failed; keyed by shape it tells you what to build, and the answer transfers to
every other destination of the same shape.
"""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum

from pydantic import BaseModel, Field

from factory.core.contract import Receipt, Verdict
from factory.core.evidence import Did


class Blocked(StrEnum):
    """Why nothing could witness, phrased as what would fix it."""

    NO_READER = "no reader admitted"
    NOTHING_FETCHED = "the step fetched nothing"
    PAINTS_ONLY = "paints, carries no structured body"
    FIELD_UNREACHABLE = "structured, but the field is not in it"


def shape_of(did: Did, receipt: Receipt) -> tuple[Blocked, tuple[str, ...]]:
    """Why this act could not be witnessed, and what the surface actually offered."""
    offered = tuple(sorted({e.content_type for e in did.exchanges if e.content_type}))
    if not receipt.reader:
        return Blocked.NO_READER, offered
    if not did.exchanges:
        return Blocked.NOTHING_FETCHED, offered
    if not any(e.structured for e in did.exchanges):
        return Blocked.PAINTS_ONLY, offered
    return Blocked.FIELD_UNREACHABLE, offered


class Demand(BaseModel):
    """One shape of surface, and how much work it is blocking."""

    blocked: Blocked
    offered: tuple[str, ...] = ()
    acts: int = 0
    fields: frozenset[str] = frozenset()


class Coverage(BaseModel):
    """What a run could and could not check."""

    confirmed: int = 0
    refuted: int = 0
    unverifiable: int = 0
    demand: dict[str, Demand] = Field(default_factory=dict)

    @property
    def acts(self) -> int:
        return self.confirmed + self.refuted + self.unverifiable

    @property
    def ceiling(self) -> float:
        """The most of this run that could ever be promoted. Unverifiable is the loss."""
        return (self.confirmed + self.refuted) / self.acts if self.acts else 0.0

    def worst(self) -> Demand | None:
        """The shape blocking the most acts: the reader worth manufacturing first."""
        return max(self.demand.values(), key=lambda d: d.acts, default=None)


def tally(seen: Iterable[tuple[Did, Receipt]]) -> Coverage:
    """Fold a run's receipts into what it could check and what it could not."""
    coverage = Coverage()
    for did, receipt in seen:
        if receipt.verdict is Verdict.CONFIRMED:
            coverage.confirmed += 1
            continue
        if receipt.verdict is Verdict.REFUTED:
            coverage.refuted += 1
            continue

        coverage.unverifiable += 1
        blocked, offered = shape_of(did, receipt)
        key = f"{blocked} [{', '.join(offered) or 'nothing'}]"
        was = coverage.demand.get(key) or Demand(blocked=blocked, offered=offered)
        coverage.demand[key] = was.model_copy(update={
            "acts": was.acts + 1, "fields": was.fields | receipt.unreadable})
    return coverage
