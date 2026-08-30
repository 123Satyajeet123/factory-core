
from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from factory.core.evidence import Run
from factory.observe import spent


class Worth(BaseModel):

    name: str
    authored: int = 1
    saved: float = 0.0
    uses: int = 0

    @property
    def returned(self) -> float:
        return self.saved * self.uses

    @property
    def recovered(self) -> bool:
        return self.returned >= self.authored

    @property
    def breakeven(self) -> int | None:
        if self.saved <= 0:
            return None
        return int(-(-self.authored // self.saved))

    def line(self) -> str:
        needs = "never" if self.breakeven is None else f"{self.breakeven} uses"
        return (f"{self.name}: authored {self.authored}, saves {self.saved:.2f}/use, "
                f"{self.uses} uses -> {self.returned:.1f} returned, breaks even at {needs}")


def needed_thinking(run: Run) -> int:
    counted = spent(run)
    return counted.model + counted.person


def worth(name: str, before: Run, after: list[Run], *, authored: int = 1) -> Worth:
    baseline = needed_thinking(before)
    if not after:
        return Worth(name=name, authored=authored, saved=0.0, uses=0)
    savings = [baseline - needed_thinking(run) for run in after]
    return Worth(name=name, authored=authored, uses=len(savings),
                 saved=sum(savings) / len(savings))


class Standing(StrEnum):

    KEEPS = "keeps"
    RETIRED = "retired"
    UNTRIED = "untried"


class Reviewed(BaseModel):

    worth: Worth
    standing: Standing

    def line(self) -> str:
        return f"{self.standing:8} {self.worth.line()}"


PATIENCE = 3


def review(worth: Worth, *, patience: int = PATIENCE) -> Reviewed:
    if worth.uses < patience:
        return Reviewed(worth=worth, standing=Standing.UNTRIED)
    if worth.saved <= 0:
        return Reviewed(worth=worth, standing=Standing.RETIRED)
    return Reviewed(worth=worth, standing=Standing.KEEPS)


def reviewed(every: list[Worth], *, patience: int = PATIENCE) -> list[Reviewed]:
    return [review(one, patience=patience) for one in every]


def retired(seen: list[Reviewed]) -> list[str]:
    return [r.worth.name for r in seen if r.standing is Standing.RETIRED]
