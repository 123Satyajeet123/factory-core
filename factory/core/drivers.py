"""Every driver protocol, in one file.

A driver that cannot be supplied is None, never a stub that raises and never a hard-wired
concrete class. The composition root decides which are present.
"""

from __future__ import annotations

from typing import Protocol

from factory.core.question import Question
from factory.core.workflow import Target


class Chooses(Protocol):
    """Decides which of the things on this page is the thing that was demonstrated.

    The one part of locating that is not plumbing. Returns the chosen candidate's key, or
    None when it will not choose -- refusing is a valid answer and must not be a guess.
    """

    def __call__(self, target: Target, among: dict[int, str]) -> int | None: ...


class Asks(Protocol):
    """Where a question goes when no driver can answer it."""

    def __call__(self, question: Question) -> str | None: ...
