
from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Verdict(StrEnum):

    CONFIRMED = "confirmed"
    REFUTED = "refuted"
    UNVERIFIABLE = "unverifiable"


class Contract(BaseModel):

    expects: dict[str, str] = Field(default_factory=dict)
    identifies: str = ""
    varies: dict[str, str] = Field(default_factory=dict)

    def for_row(self, row: Mapping[str, str]) -> Contract:
        if not self.varies:
            return self
        expects = dict(self.expects)
        for field, param in self.varies.items():
            if param in row:
                expects[field] = row[param]
        return self.model_copy(update={"expects": expects})


class Reading(BaseModel):

    values: dict[str, str] = Field(default_factory=dict)
    readable: frozenset[str] = frozenset()


class Receipt(BaseModel):

    verdict: Verdict
    channel: str = ""
    reader: str = ""
    why: str = ""
    unreadable: frozenset[str] = frozenset()
    disagreed: frozenset[str] = frozenset()
    at: datetime = Field(default_factory=lambda: datetime.now(UTC))
