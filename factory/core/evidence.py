"""Did, Exchange, Chain, StepRun, RowRun, Run."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from factory.core.contract import Receipt
from factory.core.question import Question


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


class StepRun(BaseModel):
    """One step, on one row: what was attempted, what happened, what was said of it."""

    intent: str = ""
    did: Did
    receipt: Receipt | None = None


class RowRun(BaseModel):
    """One row, and where it stopped if it did.

    A row that could not start is not a row that failed: `refused` carries the question,
    and a question is answerable where a failure is only countable.
    """

    row: dict[str, str] = Field(default_factory=dict)
    steps: list[StepRun] = Field(default_factory=list)
    refused: Question | None = None

    @property
    def ran(self) -> bool:
        return self.refused is None


class Run(BaseModel):
    """One workflow over its rows."""

    workflow: str = ""
    rows: list[RowRun] = Field(default_factory=list)

    def receipts(self) -> list[Receipt]:
        return [s.receipt for r in self.rows for s in r.steps if s.receipt]
