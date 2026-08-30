"""What makes a run stop, and which of the reasons it was.

TWO DIFFERENT THINGS. A CAP is code's, outright: how many rows, how long. Not a judgement,
not negotiable, and nothing inside a run may raise it -- a cap a workflow can rewrite is not
a cap. A GOAL is the work's: what counts as enough. Written once and checked per row by code,
because a model deciding per row whether to continue would re-reason a settled question on
every iteration and put the answer on the expensive path.

ENOUGH IS NOT FAILURE. A run that did what it was for and a run that hit a ceiling are both
ordinary, and only one of them is a problem. A system that reports "stopped" for both makes
the person work out which, every time.

GRINDING IS A STOP, AND THE CONDITION IS DERIVED. Consecutive rows that produced no receipt
at all are a run learning nothing, which is a run that will keep learning nothing. A picked
number of failures would fire on a workflow whose fourth row is legitimately hard.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from factory.core.contract import Verdict
from factory.core.evidence import Run


class Because(StrEnum):
    """Why a run ended. Distinguishable, because they need different answers."""

    #: The work is done. The only one that is not a problem.
    ENOUGH = "did what it was for"
    ROWS_RAN_OUT = "no rows left"
    CAPPED = "reached a ceiling code owns"
    REFUTED = "something irreversible did not land"
    UNANSWERED = "a question nobody could answer"
    GRINDING = "rows that learn nothing, one after another"


class Cap(BaseModel):
    """What code will not let a run exceed. Frozen, so it cannot be raised from inside."""

    model_config = {"frozen": True}

    rows: int = 1000
    #: Consecutive rows producing no receipt before the run is called grinding. Not a count
    #: of failures: a row can fail and still teach something, and that row is progress.
    learning_nothing: int = 3


class Goal(BaseModel):
    """What counts as enough, declared once rather than decided per row."""

    #: Stop after this many rows have been confirmed. Zero means every row there is.
    confirmed: int = 0

    def met(self, run: Run) -> bool:
        if not self.confirmed:
            return False
        return sum(1 for receipt in run.receipts()
                   if receipt.verdict is Verdict.CONFIRMED) >= self.confirmed


class Stopped(BaseModel):
    """That a run ended, and which condition ended it."""

    because: Because
    detail: str = ""
    rows_left: int = 0
    #: How much of the cap went unused. A ceiling only reported when it is hit is a number
    #: nobody tunes.
    room_left: int = 0

    @property
    def wanted(self) -> bool:
        """Whether this is the ending the work was for."""
        return self.because in (Because.ENOUGH, Because.ROWS_RAN_OUT)


def after_row(run: Run, *, cap: Cap, goal: Goal | None = None,
              rows_left: int = 0) -> Stopped | None:
    """Whether to stop, checked by code after each row. None means carry on."""
    room = max(0, cap.rows - len(run.rows))

    if goal is not None and goal.met(run):
        return Stopped(because=Because.ENOUGH, rows_left=rows_left, room_left=room,
                       detail=f"{goal.confirmed} confirmed")

    #: C4. Something that cannot be undone was done and the witness says it did not land.
    #: The next row would do it again, so this does not wait for the end of anything.
    for row in run.rows[-1:]:
        for step in row.steps:
            if (step.receipt is not None and step.receipt.verdict is Verdict.REFUTED
                    and step.irreversible):
                return Stopped(because=Because.REFUTED, rows_left=rows_left,
                               room_left=room, detail=step.intent or step.rung)

    if len(run.rows) >= cap.rows:
        return Stopped(because=Because.CAPPED, rows_left=rows_left, room_left=0,
                       detail=f"{cap.rows} rows")

    quiet = 0
    for row in reversed(run.rows):
        if any(step.receipt is not None for step in row.steps):
            break
        quiet += 1
    if quiet >= cap.learning_nothing:
        return Stopped(because=Because.GRINDING, rows_left=rows_left, room_left=room,
                       detail=f"{quiet} rows produced no receipt")

    unanswered = [row for row in run.rows[-1:] if row.refused is not None]
    if unanswered and quiet >= cap.learning_nothing:
        return Stopped(because=Because.UNANSWERED, rows_left=rows_left, room_left=room,
                       detail=unanswered[0].refused.because)

    return None


def ran_out(run: Run, *, cap: Cap) -> Stopped:
    """The ordinary ending: the rows were finished."""
    return Stopped(because=Because.ROWS_RAN_OUT, room_left=max(0, cap.rows - len(run.rows)),
                   detail=f"{len(run.rows)} rows")
