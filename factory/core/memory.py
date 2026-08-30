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
    TARGET = "target"
    SOURCE = "source"


class Confidence(BaseModel):
    """Receipts for and against. Never a model's report of how sure it is."""

    confirmed: int = 0
    refuted: int = 0

    @property
    def receipts(self) -> int:
        return self.confirmed + self.refuted


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
