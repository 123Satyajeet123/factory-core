"""Workflow, Step, Source, Target, Deadlines, Pace."""

from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, Field

from factory.core.contract import Contract
from factory.core.verbs import Doing


class Target(BaseModel):
    """What was demonstrated, recorded so it can be found again.

    Every field here comes from watching a person act. None of it is written by us for a
    particular destination -- that is the difference between evidence and a lookup table,
    and it is what lets the same code work on a page nobody has seen.
    """

    role: str = ""
    name: str = ""
    text: str = ""
    tag: str = ""
    #: What the target sat inside, when that is what made it unambiguous.
    within: str = ""

    def described(self) -> str:
        parts = [p for p in (self.role, repr(self.name) if self.name else "",
                             repr(self.text) if self.text else "") if p]
        return " ".join(parts) or self.tag or "an unnamed control"


class Step(BaseModel):
    """One thing to do, once per row.

    `param` names what varies between rows and `value` is what does not. Exactly one of
    them carries a write: a step holding both is a step nobody decided about, and the
    compiler refuses rather than picking.
    """

    doing: Doing
    intent: str = ""
    target: Target | None = None
    value: str = ""
    param: str = ""
    contract: Contract | None = None
    #: Present in some demonstrations and not others, so the compiler guarded it: do it if
    #: the control is there, skip it if it is not. A demonstration contains acts that are
    #: not the task -- somebody who said "watch this" still answers a message -- and
    #: treating those as mandatory is how a workflow fails on the first row that is normal.
    optional: bool = False
    #: Which surface to do it on. Empty means wherever the driver already is.
    surface: str = ""
    #: Whether doing this cannot be undone. NOT DECIDED HERE: it comes from what the
    #: compiler established about the effect from the demonstration. A list of dangerous
    #: verbs in our source would be site knowledge wearing a safety hat.
    irreversible: bool = False

    def wants(self, row: Mapping[str, str]) -> str:
        """What to write for this row."""
        return row.get(self.param, "") if self.param else self.value


class Workflow(BaseModel):
    """A body, and the parameters its rows must supply.

    Induced from several demonstrations, never written. `params` is what the compiler found
    varying; a row missing one of them is a row this workflow cannot run, which is a
    question rather than a guess.
    """

    name: str
    steps: list[Step] = Field(default_factory=list)
    params: tuple[str, ...] = ()

    def missing_from(self, row: Mapping[str, str]) -> tuple[str, ...]:
        return tuple(p for p in self.params if p not in row)
