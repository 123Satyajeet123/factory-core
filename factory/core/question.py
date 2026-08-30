"""What could not be decided, in a form something can answer.

Anything tempted to become a lookup table becomes a question instead. An answer is stored
on the workflow, so per-destination knowledge enters the system without a line of
per-destination code.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Ask(StrEnum):
    """What kind of thing is being asked. Every kind must reach a destination.

    A kind whose answer goes nowhere is a defect, not a spare.
    """

    TARGET = "target"


class Question(BaseModel):
    """One thing the system could not settle, and what it had to go on."""

    kind: Ask
    about: str
    because: str
    #: What the system could see when it gave up. A person answering needs this, and so
    #: does anything later trying to work out why the rung missed.
    candidates: tuple[str, ...] = Field(default_factory=tuple)
