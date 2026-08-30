"""Reading a workflow's rows off a destination, with the reader that already exists.

NO NEW READING MACHINERY. `witness/readers` finds records in whatever a page fetched for
itself and names no site. A source is that same act at a different moment, so this module
carries a surface, a mapping and the refusals -- and no way of reading anything.

THE CHANNEL RULE HOLDS HERE TOO. Rows are read from what the destination SENT, not from the
document of a page we just drove. A source scraped off the DOM is our own bytes coming back,
and the fact that nobody has acted yet does not make the channel a different one.

EMPTY IS NOT ZERO. A source that yields nothing and a source that could not be read are
different answers, and a run that quietly does nothing is worse than either.
"""

from __future__ import annotations

from typing import Any

from factory.core.evidence import Did
from factory.core.question import Ask, Question
from factory.core.workflow import Source, Workflow


class Rows:
    """What a source offered, or the question standing in the way."""

    def __init__(self, rows: list[dict[str, str]] | None = None,
                 question: Question | None = None) -> None:
        self.rows = rows or []
        self.question = question

    def __bool__(self) -> bool:
        return self.question is None


def _asking(source: Source, because: str, offered: tuple[str, ...] = ()) -> Question:
    return Question(kind=Ask.SOURCE, about=source.surface or "the rows",
                    because=because, candidates=offered)


async def of(browser: Any, workflow: Workflow) -> Rows:
    """The rows this workflow runs over, read from where a person said they come from."""
    source = workflow.source
    if source is None or not source.surface:
        return Rows(question=_asking(source or Source(),
                                     "nobody has said where the rows come from"))

    if not await browser.on(source.surface):
        went = await browser.go(source.surface)
        if not went.ok:
            return Rows(question=_asking(source, f"could not reach it: {went.detail}"))

    fetched = await browser.fetched()
    #: `Exchange.records()` is the reading, and it belongs to the exchange rather than to
    #: either caller -- so a witness and a source use one mechanism without importing each
    #: other, and S1 holds without a reader being passed at all.
    records = [row for exchange in fetched for row in exchange.records()]

    if not records:
        #: The same shape `witness/coverage.py` reports for a verdict it could not reach:
        #: a surface that paints its rows offers a source no more than it offers a witness.
        return Rows(question=_asking(
            source, "the destination sent no records to read",
            tuple(sorted({e.content_type for e in fetched if e.content_type}))))

    missing = source.missing_from(records)
    if missing:
        return Rows(question=_asking(
            source, f"the records carry no {', '.join(missing)}",
            tuple(sorted({key for record in records for key in record}))))

    return Rows(rows=source.rows_from(records))


def as_did(rows: Rows) -> Did:
    """A source's refusal, in the shape a run records."""
    return Did(ok=bool(rows), detail=rows.question.because if rows.question else
               f"{len(rows.rows)} rows")
