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

from factory.core.evidence import Exchange
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
    #: The surface this happened on, as its origin. A real task spans several, and an act
    #: that does not say which is an act a replay cannot place.
    surface: str = ""
    at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    #: Where the act landed, so a later reader can ask the page about the same point.
    where: tuple[float, float] | None = None
    #: The control's box when it was acted on. Observed, and never used to aim -- aiming by
    #: a recorded coordinate is what `browser/locate.py` exists to avoid. It is here because
    #: a compiler that consumes desktop recordings asks for a region, and an honest answer
    #: beats a fabricated one.
    box: tuple[float, float, float, float] | None = None
    #: What the page had fetched for itself when this act happened. NOT this act's effect:
    #: a response caused by an act arrives after it, so it lands on the NEXT act, and the
    #: gap between two consecutive acts is what the earlier one changed. That is why
    #: `compile/mine.events` needs no snapshot mechanism.
    #:
    #: WITHOUT THIS THERE IS NO CONTRACT, and therefore no verdict but UNVERIFIABLE. A
    #: demonstration is not repeatable: evidence not taken while the person was acting is
    #: gone, and every mechanism downstream can be built later from what was kept.
    saw: list[Exchange] = Field(default_factory=list)
    #: Everything else the page was offering when this act happened, described the way
    #: `browser/locate.py` describes candidates on replay.
    #:
    #: THE SAME DESCRIPTION AT BOTH ENDS. What made this target the one a person meant is a
    #: question about the set it was chosen from, and the set exists only at record time.
    #: Kept so `Target.within` and the ambiguity a question reports can be DERIVED rather
    #: than guessed at afterwards.
    among: tuple[str, ...] = ()


    @property
    def ambiguous(self) -> bool:
        """Was this control the only one of its description on the page it was pressed on?

        ANSWERABLE ONLY AT RECORD TIME, WHICH IS WHY `among` IS KEPT. `browser/locate.py`
        refuses on two matches, so a demonstration that recorded a target sharing its role
        and name with a sibling has recorded a step that CANNOT run -- and it says so on
        replay, weeks later, against somebody else's rows.

        The ordinary case is a table: a per-row control is named the same on every row, and
        a person pressing one of them knows which by where it is. Knowing that at compile
        time is what turns a silent future refusal into a question somebody can answer.
        """
        return bool(self.target) and self.among.count(self.target.described()) > 1


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
    #: What the page fetched after the LAST act, taken when recording stopped.
    #:
    #: THE LAST ACT IS THE CONSEQUENTIAL ONE. Save, send, submit -- a demonstration ends on
    #: the act that mattered, its effect arrives after it, and an effect on the far side of
    #: the final act has no next act to land on. Without this the one step worth checking is
    #: the one step that can never be checked.
    after: list[Exchange] = Field(default_factory=list)
    #: What the person said they were doing, when they said anything. Never the procedure.
    intent: str = ""
    #: Where in a factory run a person took over, when they did. Empty for a segment
    #: nobody interrupted.
    took_over_after: int | None = None

    def by_person(self) -> bool:
        return self.whose is Whose.PERSON
