"""Input shaped like a person's, for the acts no model watches.

`stealth.py` makes the browser look right; this makes the DRIVING look right. By default a
CDP press has no pointer movement at all, types a whole field in one event, and does the
next thing in the same millisecond. Nothing about the fingerprint is wrong, and no hand
has ever produced that timing.

MOVEMENT, NOT ONLY POSITION. A real pointer arrives somewhere by travelling; a synthetic
one appears at its destination. So a press here moves through points on the way and pauses
before pressing, the way a hand stops on a target.

SEEDED. The same seed gives the same path and the same delays, or a failure cannot be
re-run.
"""

from __future__ import annotations

import asyncio
import random
from typing import Any

from pydantic import BaseModel, Field, PrivateAttr


class Pace(BaseModel):
    """Timings, drawn rather than constant. Seconds."""

    travel: tuple[float, float] = (0.008, 0.022)
    dwell: tuple[float, float] = (0.06, 0.18)
    press: tuple[float, float] = (0.04, 0.11)
    rest: tuple[float, float] = (0.25, 0.9)
    steps: tuple[int, int] = (6, 14)


class Hand(BaseModel):
    """One pointer, with a position and a rhythm."""

    pace: Pace = Field(default_factory=Pace)
    seed: int | None = None
    at: tuple[float, float] = (0.0, 0.0)

    _dice: random.Random | None = PrivateAttr(default=None)

    @property
    def dice(self) -> random.Random:
        if self._dice is None:
            self._dice = random.Random(self.seed)
        return self._dice

    def draw(self, span: tuple[float, float]) -> float:
        return self.dice.uniform(*span)

    def path(self, to: tuple[float, float]) -> list[tuple[float, float]]:
        """A curve from here to there, with the overshoot-free wobble of an ordinary move.

        Quadratic, with the control point pushed off the straight line, so the trace is
        neither a line nor a spline nobody's arm could make.
        """
        (x0, y0), (x1, y1) = self.at, to
        steps = self.dice.randint(*self.pace.steps)
        sway = self.dice.uniform(-0.18, 0.18)
        cx = (x0 + x1) / 2 - (y1 - y0) * sway
        cy = (y0 + y1) / 2 + (x1 - x0) * sway
        points = []
        for step in range(1, steps + 1):
            t = step / steps
            u = 1 - t
            points.append((u * u * x0 + 2 * u * t * cx + t * t * x1,
                           u * u * y0 + 2 * u * t * cy + t * t * y1))
        return points

    async def reach(self, cdp: Any, session_id: str, to: tuple[float, float]) -> int:
        """Travel to a point. Returns how many moves were sent."""
        moves = self.path(to)
        for x, y in moves:
            await cdp.send.Input.dispatchMouseEvent(
                params={"type": "mouseMoved", "x": x, "y": y},
                session_id=session_id)
            await asyncio.sleep(self.draw(self.pace.travel))
        self.at = to
        await asyncio.sleep(self.draw(self.pace.dwell))
        return len(moves)

    async def press_at(self, cdp: Any, session_id: str, to: tuple[float, float],
                       button: str = "left") -> None:
        """Press where the pointer already is. Travel first; this does not move."""
        x, y = to
        await cdp.send.Input.dispatchMouseEvent(
            params={"type": "mousePressed", "x": x, "y": y,
                    "button": button, "clickCount": 1},
            session_id=session_id)
        await asyncio.sleep(self.draw(self.pace.press))
        await cdp.send.Input.dispatchMouseEvent(
            params={"type": "mouseReleased", "x": x, "y": y,
                    "button": button, "clickCount": 1},
            session_id=session_id)

    async def rest(self) -> None:
        """The gap between one act and the next."""
        await asyncio.sleep(self.draw(self.pace.rest))


def _self_check() -> None:
    """H3, H4, H5 need no browser: the path and the draws are pure.

        uv run python -m factory.browser.hand
    """
    a, b = Hand(seed=7), Hand(seed=7)
    assert a.path((300, 200)) == b.path((300, 200)), "H5 same seed, same path"
    assert [a.draw(a.pace.dwell) for _ in range(5)] == \
           [b.draw(b.pace.dwell) for _ in range(5)], "H5 same seed, same delays"

    fresh = Hand(seed=11)
    drawn = [fresh.draw(fresh.pace.dwell) for _ in range(8)]
    assert len(set(drawn)) > 1, "H4 timing is drawn, not constant"
    lo, hi = fresh.pace.dwell
    assert all(lo <= d <= hi for d in drawn), "H4 draws stay in their span"

    walk = Hand(seed=3)
    points = walk.path((400, 120))
    assert len(points) >= walk.pace.steps[0], "H1 a path has intermediate points"
    assert len(set(points)) == len(points), "H1 the pointer actually moves"
    assert points[-1] == (400, 120), "H3 the path ends on the given point"
    off_line = any(abs(y - (120 * x / 400)) > 0.5 for x, y in points[:-1])
    assert off_line, "a straight line is not what an arm makes"
    print("hand: H1 H3 H4 H5 ok")


if __name__ == "__main__":
    _self_check()
