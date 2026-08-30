"""Contract, Reading, Verdict, Receipt. What a step claims, and what was seen of it."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Verdict(StrEnum):
    """Three values, and the third is not a softer version of the second.

    UNVERIFIABLE means no channel that could witness this act could see the fields it
    expects. It moves neither side of `core/memory.Confidence`, so it is invisible to
    promotion unless something counts it separately -- and it is the ceiling on promotion,
    which is the ceiling on cheapness.
    """

    CONFIRMED = "confirmed"
    REFUTED = "refuted"
    UNVERIFIABLE = "unverifiable"


class Contract(BaseModel):
    """What must be true after a step, as fields rather than as prose.

    Derived from what the demonstration saw, never written by hand and never asked of a
    model. A contract that expects nothing is unverifiable by construction: a check anything
    passes selects for acts that do nothing.
    """

    expects: dict[str, str] = Field(default_factory=dict)
    #: The field whose value exists only because this act wrote it, when the destination
    #: issued one and the demonstration observed it.
    #:
    #: WITHOUT IT, CONFIRMED MEANS PRESENT AND NOT CAUSED. A record already holding the
    #: expected values satisfies the contract, and no reader can tell the two apart -- the
    #: difference is in what was bound, not in what was read. Naming the field here keeps
    #: the weaker confirmation visible instead of letting one word mean both.
    identifies: str = ""
    #: field -> the parameter whose value belongs there, for a step that varies by row.
    #:
    #: A CONTRACT DERIVED FROM ONE DEMONSTRATION BINDS THAT DEMONSTRATION'S VALUE. Left
    #: alone it confirms every later row against the demonstrated record: measured, two
    #: rows writing other names came back CONFIRMED against `name = 'Grace Hopper'`, which
    #: was true and had nothing to do with either of them.
    varies: dict[str, str] = Field(default_factory=dict)

    def for_row(self, row: Mapping[str, str]) -> Contract:
        """This contract, bound to what THIS row was supposed to write."""
        if not self.varies:
            return self
        expects = dict(self.expects)
        for field, param in self.varies.items():
            if param in row:
                expects[field] = row[param]
        return self.model_copy(update={"expects": expects})


class Reading(BaseModel):
    """What one reader saw, and -- separately -- what it was able to look at.

    `readable` carries the whole distinction this driver rests on. An expected field missing from
    `values` because the reader looked and it was not there REFUTES. The same field missing
    because the reader cannot address that kind of field at all is blindness and must not.
    Without the second set those are the same bytes, and a reader guesses.
    """

    values: dict[str, str] = Field(default_factory=dict)
    readable: frozenset[str] = frozenset()


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
    reader: str = ""
    why: str = ""
    unreadable: frozenset[str] = frozenset()
    disagreed: frozenset[str] = frozenset()
    at: datetime = Field(default_factory=lambda: datetime.now(UTC))
