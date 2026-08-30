"""Did, Exchange, Chain, StepRun, RowRun, Run."""

from __future__ import annotations

import csv
import io
import json
from enum import StrEnum
from typing import Any

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
    #: What went wrong on the page while this act happened. A step that succeeded while the
    #: page's own JavaScript threw, or while a request never answered, is otherwise
    #: indistinguishable from one that worked -- and a 404 is visible where a dropped
    #: connection is not, because only one of them has a status.
    complained: list[str] = Field(default_factory=list)


#: Content types that carry fields rather than pixels. One list: `browser/bodies.py` uses
#: it to decide what to keep, `witness/coverage.py` to say what a surface offered. Two
#: copies would disagree the first time one grew an entry.
STRUCTURED = ("json", "csv", "xml", "x-ndjson", "plain")


#: A list of objects is a record set when they agree on keys. One object is not a set, and
#: two objects sharing nothing are two things that happen to be adjacent.
ENOUGH_SHARED = 1


def record_sets(body: Any) -> list[dict[str, str]]:
    """Every record set anywhere in a parsed structured body, flattened."""
    found: list[dict[str, str]] = []
    stack = [body]
    while stack:
        seen = stack.pop()
        if isinstance(seen, dict):
            stack.extend(seen.values())
        elif isinstance(seen, list):
            rows = [row for row in seen if isinstance(row, dict)]
            shared = set.intersection(*(set(r) for r in rows)) if rows else set()
            if len(rows) > 1 and len(shared) >= ENOUGH_SHARED:
                found.extend({str(k): str(v) for k, v in row.items()} for row in rows)
            elif len(rows) == 1:
                found.append({str(k): str(v) for k, v in rows[0].items()})
            stack.extend(item for item in seen if not isinstance(item, dict))
    return found


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

    def records(self) -> list[dict[str, str]]:
        """The record sets this response carries. JSON if it parses, CSV if it does not.

        ONE EXTRACTOR, TWO CALLERS, AND THAT IS THE POINT. `witness/readers/fetched.py`
        asks this to CHECK an act and `compile/mine.py` asks it to DERIVE what to check.
        Two copies would let a compiler bind a field its own reader cannot address, and
        the disagreement would read as blindness rather than as a bug.
        """
        if not self.body:
            return []
        try:
            return record_sets(json.loads(self.body))
        except (ValueError, TypeError):
            pass
        try:
            rows = list(csv.DictReader(io.StringIO(self.body)))
        except (csv.Error, ValueError):
            return []
        return [{str(k): str(v) for k, v in row.items() if k} for row in rows if row]


Did.model_rebuild()


class StepRun(BaseModel):
    """One step, on one row: what was attempted, what happened, what was said of it.

    `rung` is which mechanism resolved the control -- remembered, chosen, structural. It is
    named by `run/select.py` and was being dropped here, which made "how much of this run
    needed a model" underivable from a Run and left `observe.py` reporting it as unknown.
    Empty means nothing recorded one, and `observe` counts that rather than assuming free.
    """

    intent: str = ""
    did: Did
    receipt: Receipt | None = None
    rung: str = ""


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
