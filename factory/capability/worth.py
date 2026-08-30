
from __future__ import annotations

import difflib

from pydantic import BaseModel

from factory.core.workflow import Workflow

SAME = 0.85


class Judged(BaseModel):

    stock: tuple[str, ...] = ()
    duplicate: str = ""
    likeness: float = 0.0

    def __bool__(self) -> bool:
        return not self.stock and not self.duplicate

    def why(self) -> str:
        if self.duplicate:
            return f"{self.likeness:.0%} the same as {self.duplicate}"
        if self.stock:
            return "; ".join(self.stock)
        return "encodes something, and nothing else encodes it"


def shape(workflow: Workflow) -> tuple[str, ...]:
    return tuple(
        f"{step.doing.value}:{step.target.role}:{step.target.name}" if step.target
        else step.doing.value
        for step in workflow.steps)


def stock(workflow: Workflow) -> tuple[str, ...]:
    reasons = []
    if len(workflow.steps) <= 1:
        reasons.append("one step is an act, not a procedure")
    if not workflow.params:
        reasons.append("no parameters, so it does the same thing every time")
    surfaces = {step.surface for step in workflow.steps if step.surface}
    if len(workflow.steps) <= 2 and len(surfaces) <= 1:
        reasons.append("two steps on one surface is what any page offers")
    return tuple(reasons)


def closest(candidate: tuple[str, ...],
            installed: dict[str, tuple[str, ...]]) -> tuple[str, float]:
    best, ratio = "", 0.0
    for name, other in installed.items():
        alike = difflib.SequenceMatcher(None, candidate, other).ratio()
        if alike > ratio:
            best, ratio = name, alike
    return best, ratio


def judge(workflow: Workflow, installed: dict[str, tuple[str, ...]] | None = None,
          *, same: float = SAME) -> Judged:
    reasons = stock(workflow)
    if reasons:
        return Judged(stock=reasons)
    name, alike = closest(shape(workflow), installed or {})
    if alike >= same:
        return Judged(duplicate=name, likeness=alike)
    return Judged(likeness=alike)
