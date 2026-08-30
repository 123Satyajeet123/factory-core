"""Workflow, Step, Source, Target, Deadlines, Pace."""

from __future__ import annotations

from pydantic import BaseModel


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
