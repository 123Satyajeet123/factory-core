"""A person's consent to an irreversible effect, with a budget.

NOT AUTHORISATION. A policy engine answers "is this principal allowed this action on this
resource" from a rule somebody wrote. The question here is whether a PERSON consented to
this effect, how many times, and whether that consent is still good. Measured in
gates/permits.md: casbin has no notion of a grant that depletes, and oso ships no wheel for
this interpreter.

CONSUMED, NOT HELD. A permit carries a budget and the budget goes down. "You may email
these nine people" and "you may email" are different sentences, and only one of them is a
permit.

ABSENCE REFUSES. No permit means the act does not happen. Not a warning, not a log line,
and not a default-allow with a flag for turning it off.

THE AGENT NEVER HOLDS THIS. `run/harness.py` checks before the act reaches the driver. It is
not a tool a model may call and not a field a model may set -- one that can grant its own
permission has none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from pydantic import BaseModel

from factory.core.memory import Entry, Kind, Tier
from factory.core.question import Ask, Question
from factory.core.workflow import Step


class Permit(BaseModel):
    """What a person allowed, how much of it is left, and until when."""

    #: What was consented to, in the words the person was shown.
    about: str
    granted: int
    spent: int = 0
    until: datetime | None = None

    @property
    def left(self) -> int:
        return max(0, self.granted - self.spent)

    def good(self, now: datetime | None = None) -> bool:
        when = now or datetime.now(UTC)
        return self.left > 0 and (self.until is None or when < self.until)


def _key(step: Step) -> str:
    """One permit per thing being consented to, not one per row.

    Keyed by what the step DOES and where -- so nine sends of the same step spend one
    permit nine times, and a different irreversible step needs its own.
    """
    where = step.target.described() if step.target else step.surface or "?"
    return f"{step.doing.value}:{where}"


def asked_for(step: Step, workflow: str) -> Question:
    """What a person is being asked, in terms of the act rather than of the machinery."""
    where = step.target.described() if step.target else step.surface
    return Question(
        kind=Ask.PERMIT,
        about=f"{step.intent or step.doing.value} -- {where}".strip(" -"),
        because=f"{workflow!r} does this and it cannot be undone",
        candidates=(f"step {_key(step)}",))


def held(memory: object, step: Step, workflow: str) -> Permit | None:
    """The permit covering this step, if one is still good."""
    entry = memory.recall(Kind.PERMIT, _key(step), workflow=workflow)  # type: ignore[attr-defined]
    if entry is None:
        return None
    permit = Permit.model_validate(entry.value)
    return permit if permit.good() else None


def grant(memory: object, step: Step, workflow: str, *, times: int,
          days: float | None = None) -> Permit:
    """Record what a person allowed. Only ever called with an answer in hand."""
    permit = Permit(
        about=asked_for(step, workflow).about, granted=times,
        until=datetime.now(UTC) + timedelta(days=days) if days else None)
    memory.remember(Kind.PERMIT, _key(step), permit.model_dump(mode="json"),  # type: ignore[attr-defined]
                    tier=Tier.WORKFLOW, scope=workflow)
    return permit


def spend(memory: object, step: Step, workflow: str) -> Permit | None:
    """Use one. Returns what is left, or nothing if there was nothing to use."""
    permit = held(memory, step, workflow)
    if permit is None:
        return None
    spent = permit.model_copy(update={"spent": permit.spent + 1})
    memory.remember(Kind.PERMIT, _key(step), spent.model_dump(mode="json"),  # type: ignore[attr-defined]
                    tier=Tier.WORKFLOW, scope=workflow)
    return spent


def revoke(memory: object, step: Step, workflow: str) -> None:
    """Withdraw it. The next act is refused; there is no grace."""
    entry: Entry | None = memory.at(Kind.PERMIT, _key(step), Tier.WORKFLOW, workflow)  # type: ignore[attr-defined]
    if entry is not None:
        memory.forget(entry)  # type: ignore[attr-defined]
