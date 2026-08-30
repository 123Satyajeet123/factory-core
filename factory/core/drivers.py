"""Every driver protocol, in one file.

A driver that cannot be supplied is None, never a stub that raises and never a hard-wired
concrete class. The composition root decides which are present.
"""

from __future__ import annotations

from typing import Protocol

from factory.core.question import Question


class Chooses(Protocol):
    """Decides which of the things on this page is the thing that was demonstrated.

    The one part of locating that is not plumbing. Returns the chosen candidate's key, or
    None when it will not choose -- refusing is a valid answer and must not be a guess.

    `wanted` IS A DESCRIPTION, NOT A TARGET, and that is the whole difference between a
    chooser that can answer and one that cannot. A `Target` with no name describes itself as
    "button", and a model handed "button" against two buttons correctly says none of these
    -- measured. What identifies the step is what the person was DOING, which lives on the
    step rather than on its target.

    ASYNC BECAUSE THE ANSWER COMES OVER A NETWORK. `find` is already a coroutine, so a
    synchronous chooser either blocks the loop for the length of a model call or has to
    start a second one inside the first, which raises. The impedance was real and this is
    where it belongs.
    """

    async def __call__(self, wanted: str, among: dict[int, str]) -> int | None: ...


class Asks(Protocol):
    """Where a question goes when no driver can answer it."""

    def __call__(self, question: Question) -> str | None: ...
