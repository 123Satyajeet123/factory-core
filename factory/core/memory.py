"""Entry, Tier, Scope, Confidence. What is known, at what scope, on what evidence."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Tier(StrEnum):
    """Three tiers, narrowest first. The words are the operator's own.

    Resolution walks EXECUTION, then WORKFLOW, then MAIN, and the first hit wins -- so a
    run may override a workflow and a workflow may override the person's defaults, without
    anything being copied between them.
    """

    EXECUTION = "execution"
    WORKFLOW = "workflow"
    MAIN = "main"


class Kind(StrEnum):
    """What a thing known ABOUT is. One value per question somebody can answer."""

    PACE = "pace"
    #: A person's consent to an irreversible effect, with a budget. Held here because a
    #: permit is a thing known at a scope, and the tiers, the store and the scope chain
    #: already exist -- a second store for consent would be a second thing to keep true.
    PERMIT = "permit"
    CADENCE = "cadence"
    TARGET = "target"
    #: Where in a body a field the contract names actually sits. Learned from an act
    #: nobody could read, so the next run of the same surface can.
    READING = "reading"
    SOURCE = "source"


class Confidence(BaseModel):
    """Receipts for and against. Never a model's report of how sure it is.

    `caused` is the subset of `confirmed` where the contract named an idempotency field --
    a value that exists only because the act wrote it. The rest confirm that the world is
    CONSISTENT with the act having worked, which is a weaker claim wearing the same word.
    Counted apart so a policy can demand the stronger one, and so the share of promotion
    resting on the weaker one is visible rather than assumed away.
    """

    confirmed: int = 0
    refuted: int = 0
    caused: int = 0

    @property
    def receipts(self) -> int:
        return self.confirmed + self.refuted

    @property
    def present_only(self) -> int:
        """Confirmations that could not tell caused from already there."""
        return self.confirmed - self.caused


class Entry(BaseModel):
    """One thing known, at one scope."""

    kind: Kind
    tier: Tier
    #: Empty at MAIN, a workflow name at WORKFLOW, a run id at EXECUTION.
    scope: str = ""
    key: str
    value: Any = None
    confidence: Confidence = Field(default_factory=Confidence)
    at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    until: datetime | None = None

    def standing(self, now: datetime | None = None) -> bool:
        return self.until is None or (now or datetime.now(UTC)) < self.until
