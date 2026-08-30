"""What a run cost, in a unit that was measured rather than assigned.

TWO JOBS, AND CONFLATING THEM IS WHY OBSERVABILITY USUALLY MEANS ONLY THE SECOND. THE TALLY
is here: what a run cost, whether the next one cost less, and how much of it needed nobody.
THE TRACE -- where it spent, over OTLP -- is a different job and a different file.

THE UNIT IS SECONDS, AND A RUNG'S COST IS OBSERVED. See gates/cost-model.md. A table
assigning each rung a name is a number that was picked, and this system already reasons in
milliseconds everywhere -- 9.6ms per playwright op, 1116ms for one guarded act, 1ms for
rung 0. The unit existed; only the model was invented.

A PRIOR IS ALLOWED AND MUST LOSE. Before a rung has been seen there is no median, and
saying nothing is useless. So an ordering stands in, marked as a prior, and the first real
observation replaces it. What is never done is reporting a prior as though it were measured.

A PERSON IS NOT AN EXPENSIVE MODEL. They are slower by orders of magnitude, they may not
answer at all, and "this workflow stopped needing a person" is the largest thing this
system can report. Summed into one number it is invisible: a run that traded a person for
three model calls looks worse and is enormously better. So the two are never added.
"""

from __future__ import annotations

import statistics
from enum import StrEnum

from pydantic import BaseModel, Field

from factory.core.contract import Verdict
from factory.core.evidence import Run


class Answered(StrEnum):
    """Who or what answered a step. Words for a person to read, never an arithmetic."""

    CACHE = "cache"
    MACHINE = "machine"
    MODEL = "model"
    PERSON = "person"


#: Which rung is answered by what. This is a naming, not a cost -- the cost is measured.
BY = {
    "remembered": Answered.CACHE,
    "none": Answered.CACHE,
    "structural": Answered.MACHINE,
    "accessible": Answered.MACHINE,
    "chosen": Answered.MODEL,
    "asked": Answered.PERSON,
}

#: Seconds, used ONLY until a rung has been observed. Ordered, deliberately coarse, and
#: visibly a guess: `Priced.prior` is true for any number that came from here.
PRIOR = {
    Answered.CACHE: 0.001,
    Answered.MACHINE: 0.010,
    Answered.MODEL: 2.0,
    Answered.PERSON: 60.0,
}


class Priced(BaseModel):
    """What one rung costs, and whether anybody has actually seen it cost that."""

    rung: str
    seconds: float
    observations: int = 0

    @property
    def prior(self) -> bool:
        """True while this is a guess. Never reported as a measurement."""
        return self.observations == 0

    def line(self) -> str:
        how = f"{self.observations} seen" if self.observations else "PRIOR, unobserved"
        return f"{self.rung:12} {self.seconds * 1000:8.1f} ms  ({how})"


class Prices(BaseModel):
    """What every rung costs, learned from runs. Priors until they are not."""

    seen: dict[str, list[float]] = Field(default_factory=dict)

    def observe(self, rung: str, seconds: float) -> None:
        self.seen.setdefault(rung or "none", []).append(seconds)

    def of(self, rung: str) -> Priced:
        """The median observed, or the prior for whatever answers this rung."""
        took = self.seen.get(rung or "none", [])
        if took:
            return Priced(rung=rung or "none", seconds=statistics.median(took),
                          observations=len(took))
        answered = BY.get(rung or "none")
        if answered is None:
            #: X4. An unknown rung is charged at the worst thing actually seen, or at the
            #: worst prior when nothing has been. Derived, never chosen.
            worst = max((statistics.median(v) for v in self.seen.values()), default=0.0)
            return Priced(rung=rung or "unknown", seconds=max(worst, max(PRIOR.values())))
        return Priced(rung=rung or "none", seconds=PRIOR[answered])


class Spend(BaseModel):
    """What one run cost, and who paid it. Never one number."""

    steps: int = 0
    seconds: float = 0.0
    by_rung: dict[str, int] = Field(default_factory=dict)
    #: X3. Counted apart, always, and never added together.
    model: int = 0
    person: int = 0
    machine: int = 0

    confirmed: int = 0
    refuted: int = 0
    unverifiable: int = 0
    #: Steps whose cost came from a prior rather than an observation.
    estimated: int = 0

    def said(self) -> str:
        """One line. Both of the numbers that matter, because neither means anything alone."""
        guessed = f", {self.estimated} estimated" if self.estimated else ""
        return (f"{self.steps} steps in {self.seconds * 1000:.0f} ms: "
                f"{self.machine} by machine, {self.model} by model, {self.person} by person"
                f" | checked {self.confirmed + self.refuted}, "
                f"could not check {self.unverifiable}{guessed}")


def spent(run: Run, prices: Prices | None = None) -> Spend:
    """Fold a run into what it cost and what it could show for it."""
    prices = prices or Prices()
    tally = Spend()
    for row in run.rows:
        for step in row.steps:
            rung = step.rung or "none"
            priced = prices.of(rung)
            tally.steps += 1
            tally.seconds += priced.seconds
            tally.estimated += priced.prior
            tally.by_rung[rung] = tally.by_rung.get(rung, 0) + 1
            match BY.get(rung):
                case Answered.PERSON:
                    tally.person += 1
                case Answered.MODEL:
                    tally.model += 1
                case Answered.CACHE | Answered.MACHINE:
                    tally.machine += 1
                case _:
                    #: An unnamed rung is charged as the worst, so it is not "by machine".
                    tally.model += 1
            if step.receipt is None:
                continue
            match step.receipt.verdict:
                case Verdict.CONFIRMED:
                    tally.confirmed += 1
                case Verdict.REFUTED:
                    tally.refuted += 1
                case _:
                    tally.unverifiable += 1
    return tally


def cheaper(earlier: Spend, later: Spend) -> bool | None:
    """Whether the later run cost less. None when either side is all guesswork.

    A direction derived from two priors is a direction about `PRIOR`, not about the system.
    """
    if earlier.estimated == earlier.steps and later.estimated == later.steps:
        return None
    return later.seconds < earlier.seconds
