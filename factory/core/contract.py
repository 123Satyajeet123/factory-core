"""Contract, Found, Verdict, Receipt. What a step claims, and what was seen of it."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Verdict(StrEnum):
    """Three values, and the third is not a softer version of the second.

    UNVERIFIABLE means no channel that could witness this act could see the fields it
    binds. It moves neither side of `core/memory.Confidence`, so it is invisible to
    promotion unless something counts it separately -- and it is the ceiling on promotion,
    which is the ceiling on cheapness.
    """

    CONFIRMED = "confirmed"
    REFUTED = "refuted"
    UNVERIFIABLE = "unverifiable"


class Contract(BaseModel):
    """What must be true after a step, as fields rather than as prose.

    Derived from what the demonstration saw, never written by hand and never asked of a
    model. A contract that binds nothing is unverifiable by construction: a check anything
    passes selects for acts that do nothing.
    """

    binds: dict[str, str] = Field(default_factory=dict)


class Found(BaseModel):
    """What one reader saw, and -- separately -- what it was able to look at.

    `saw` carries the whole distinction the machine rests on. A bound field missing from
    `values` because the reader looked and it was not there REFUTES. The same field missing
    because the reader cannot address that kind of field at all is blindness and must not.
    Without the second set those are the same bytes, and a reader guesses.
    """

    values: dict[str, str] = Field(default_factory=dict)
    saw: frozenset[str] = frozenset()


class Receipt(BaseModel):
    """One reading, by one rung, at one time.

    A verdict is what was visible when it was taken, never a permanent fact about the act.
    A confirmation arriving later -- a webhook, a nightly export, a record visible only on
    the next load -- is a SECOND receipt rather than a fourth verdict, because
    `core/memory.Confidence` already counts receipts and a pending state would have to be
    handled by everything downstream to be handled anywhere.
    """

    verdict: Verdict
    channel: str = ""
    rung: str = ""
    why: str = ""
    unseen: frozenset[str] = frozenset()
    disagreed: frozenset[str] = frozenset()
    at: datetime = Field(default_factory=lambda: datetime.now(UTC))
