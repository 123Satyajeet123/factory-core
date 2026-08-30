"""What a person did, as acts a program can be derived from.

RECORDED, NEVER DESCRIBED. Every field here comes from watching. Nothing is a person's
account of what they did, because the account is where the procedure a model would have
invented gets in.

AN ACT IS NOT A STEP. A step is what a compiler decides after seeing several acts across
several iterations -- which repeated, which varied, which was incidental. Keeping them
apart is what lets `compile/` refuse: with one shape for both, every act is already a step
and refusing is impossible.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from factory.core.verbs import Doing
from factory.core.workflow import Target


class Act(BaseModel):
    """One thing a person did, and what it was done to.

    `target` is resolved from the accessibility tree at the moment of the act, not guessed
    from tag names afterwards: the name a page reports later is a different name, and the
    one that matters is the one `locate` will search for on replay.
    """

    doing: Doing
    target: Target | None = None
    value: str = ""
    at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    #: Where the act landed, so a later reader can ask the page about the same point.
    where: tuple[float, float] | None = None
    #: The control's box when it was acted on. Observed, and never used to aim -- aiming by
    #: a recorded coordinate is what `browser/locate.py` exists to avoid. It is here because
    #: a compiler that consumes desktop recordings asks for a region, and an honest answer
    #: beats a fabricated one.
    box: tuple[float, float, float, float] | None = None


class Whose(StrEnum):
    """Who was driving. A ledger that cannot say is a ledger that cannot be learned from."""

    PERSON = "person"
    FACTORY = "factory"


class Segment(BaseModel):
    """A run of acts with one author.

    Taking the wheel ends a segment and starts another, which is what lets a correction
    re-enter the compiler as evidence instead of being lost as an interruption -- and what
    keeps `browser/pace.py` from fitting the factory's own driving.
    """

    whose: Whose = Whose.PERSON
    acts: list[Act] = Field(default_factory=list)
    #: What the person said they were doing, when they said anything. Never the procedure.
    intent: str = ""

    def by_person(self) -> bool:
        return self.whose is Whose.PERSON
