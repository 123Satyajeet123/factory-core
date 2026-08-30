
from __future__ import annotations

import statistics
from enum import StrEnum

from pydantic import BaseModel, Field

from factory.core.contract import Verdict
from factory.core.evidence import Run


class Answered(StrEnum):

    CACHE = "cache"
    MACHINE = "machine"
    MODEL = "model"
    PERSON = "person"


UNRECORDED = "unrecorded"

BY = {
    "remembered": Answered.CACHE,
    "none": Answered.CACHE,
    "structural": Answered.MACHINE,
    "accessible": Answered.MACHINE,
    "chosen": Answered.MODEL,
    "asked": Answered.PERSON,
}

PRIOR = {
    Answered.CACHE: 0.001,
    Answered.MACHINE: 0.010,
    Answered.MODEL: 2.0,
    Answered.PERSON: 60.0,
}


class Priced(BaseModel):

    rung: str
    seconds: float
    observations: int = 0

    @property
    def prior(self) -> bool:
        return self.observations == 0

    def line(self) -> str:
        how = f"{self.observations} seen" if self.observations else "PRIOR, unobserved"
        return f"{self.rung:12} {self.seconds * 1000:8.1f} ms  ({how})"


class Prices(BaseModel):

    seen: dict[str, list[float]] = Field(default_factory=dict)

    def observe(self, rung: str, seconds: float) -> None:
        self.seen.setdefault(rung or UNRECORDED, []).append(seconds)

    def of(self, rung: str) -> Priced:
        rung = rung or UNRECORDED
        took = self.seen.get(rung, [])
        if took:
            return Priced(rung=rung, seconds=statistics.median(took), observations=len(took))
        answered = BY.get(rung)
        if answered is None:
            worst = max((statistics.median(v) for v in self.seen.values()), default=0.0)
            return Priced(rung=rung, seconds=max(worst, max(PRIOR.values())))
        return Priced(rung=rung, seconds=PRIOR[answered])


class Spend(BaseModel):

    steps: int = 0
    seconds: float = 0.0
    by_rung: dict[str, int] = Field(default_factory=dict)
    model: int = 0
    person: int = 0
    machine: int = 0

    confirmed: int = 0
    refuted: int = 0
    unverifiable: int = 0
    estimated: int = 0

    def said(self) -> str:
        guessed = f", {self.estimated} estimated" if self.estimated else ""
        return (f"{self.steps} steps in {self.seconds * 1000:.0f} ms: "
                f"{self.machine} by machine, {self.model} by model, {self.person} by person"
                f" | checked {self.confirmed + self.refuted}, "
                f"could not check {self.unverifiable}{guessed}")


def spent(run: Run, prices: Prices | None = None) -> Spend:
    prices = prices or Prices()
    tally = Spend()
    for row in run.rows:
        for step in row.steps:
            rung = step.rung or UNRECORDED
            tally.steps += 1
            if step.seconds > 0:
                tally.seconds += step.seconds
            else:
                priced = prices.of(rung)
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
    if earlier.estimated == earlier.steps and later.estimated == later.steps:
        return None
    return later.seconds < earlier.seconds
