"""Which of these is the control the demonstration meant?

THE MODEL SEES DESCRIPTIONS, NEVER THE PAGE. It is handed the lines `locate` already offers
-- role and name -- so its answer is an index into a set the driver holds, and there is no
way for it to name a selector, a coordinate or a destination.

"NONE OF THESE" IS AN ANSWER. D7: a confident wrong index presses the wrong control and
`browser/guard.py` cannot catch it -- the guard checks we hit what we aimed at, not that we
aimed at the right thing. Refusing has to be as easy to say as choosing, or the cheap answer
is always to pick something.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Chosen(BaseModel):
    """Which candidate, or none."""

    which: int = Field(description="index of the candidate that matches, or -1 if none do")
    because: str = Field(default="", description="what in the description decided it")

    def picked(self) -> int | None:
        return None if self.which < 0 else self.which


ASKING = """A step recorded on a page was described as: {wanted}

The page now offers these controls, by position:
{among}

Which position is the control that step meant? Answer -1 if none of them is it.
Do not guess: a wrong choice presses the wrong control and there is no way to undo it."""


def situation(wanted: str, among: dict[int, str]) -> str:
    lines = "\n".join(f"  {i}: {line}" for i, line in sorted(among.items()))
    return ASKING.format(wanted=wanted, among=lines)
