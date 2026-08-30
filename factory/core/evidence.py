"""Did, Exchange, Chain, StepRun, RowRun, Run."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Delivery(StrEnum):
    """How an act reached the page, or why it did not.

    Vocabulary shared with the guard. `ok` alone never means delivered: a caller reads
    `delivery` before reporting success.
    """

    TARGET_HIT = "target_hit"
    INTERCEPTED = "intercepted"
    OFF_TARGET = "off_target"
    NOT_SETTLED = "not_settled"
    NOT_PROBED = "not_probed"


class Landed(BaseModel):
    """The outcome of one guarded dispatch.

    `dispatched` is the safety-critical field: false means nothing was sent, so a caller
    must return before evaluating any postcondition.
    """

    dispatched: bool
    delivery: Delivery
    why: str = ""
    at: tuple[float, float] | None = None
    moves: int = 0


class Did(BaseModel):
    """One act, performed and read back."""

    ok: bool
    detail: str = ""
    value: str | None = None
    delivery: Delivery = Delivery.NOT_PROBED
    exchanges: list[Exchange] = Field(default_factory=list)


#: Content types that carry fields rather than pixels. One list: `browser/bodies.py` uses
#: it to decide what to keep, `witness/coverage.py` to say what a surface offered. Two
#: copies would disagree the first time one grew an entry.
STRUCTURED = ("json", "csv", "xml", "x-ndjson", "plain")


class Exchange(BaseModel):
    """One response the page fetched for itself."""

    url: str
    status: int
    content_type: str = ""
    size: int = 0
    body: str | None = None

    @property
    def structured(self) -> bool:
        """Whether this response carries fields something could read."""
        return any(mark in self.content_type for mark in STRUCTURED)


Did.model_rebuild()
