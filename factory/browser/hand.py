"""Input shaped like a person's, for the acts no model watches.

`stealth.py` makes the browser look right; this makes the DRIVING look right, and they are
different problems. By default a CDP press has no pointer movement at all, types a whole
field in one event, and does the next thing in the same millisecond. Nothing about the
fingerprint is wrong, and no hand has ever produced that timing.

THE POINTER IS A SHADOW. Every event here goes into the page over CDP. The operator's own
cursor never moves, which is why a library that drives the OS cursor was disqualified in
gates/pointer-motion.md however good its curves.

WHAT IS THE VENDOR'S AND WHAT IS OURS. ghost-cursor supplies the curve, measured to put its
velocity peak mid-path where ours put it at the end. It supplies no overshoot, no timing
and no seed, so those are here.
"""

from __future__ import annotations

import asyncio
import math
import random
from typing import Any

from pydantic import BaseModel, Field, PrivateAttr

from factory.browser import motion


class Pace(BaseModel):
    """Timings in seconds. Spans are medians to draw around, not hard bounds."""

    #: Fitts: a + b * log2(1 + distance / width). Seconds.
    travel_base: float = 0.09
    travel_scale: float = 0.045
    travel_width: float = 45.0

    dwell: tuple[float, float] = (0.06, 0.20)
    press: tuple[float, float] = (0.04, 0.11)
    rest: tuple[float, float] = (0.25, 0.90)
    keystroke: tuple[float, float] = (0.05, 0.16)

    #: How far off centre a press may land, as a fraction of the target's box.
    aim_spread: float = 0.16
    #: Longer moves overshoot more often. Probability caps here.
    overshoot_max: float = 0.35


class Hand(BaseModel):
    """One shadow pointer, with a position and a rhythm."""

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
        """Log-normal around the middle of the span. Human gaps are right-skewed."""
        lo, hi = span
        return max(lo * 0.5, ((lo + hi) / 2) * self.dice.lognormvariate(0.0, 0.30))

    def aim(self) -> tuple[float, float]:
        """Where in the target to land. Never the exact centre twice."""
        spread = self.pace.aim_spread
        return (min(0.85, max(0.15, 0.5 + self.dice.gauss(0, spread))),
                min(0.85, max(0.15, 0.5 + self.dice.gauss(0, spread))))

    def travel_time(self, distance: float) -> float:
        """Fitts. Longer moves take longer, and sublinearly."""
        return self.pace.travel_base + self.pace.travel_scale * math.log2(
            1 + distance / self.pace.travel_width)

    def _overshoots(self, distance: float) -> bool:
        return self.dice.random() < min(self.pace.overshoot_max, distance / 2500)

    def _past(self, to: tuple[float, float], distance: float) -> tuple[float, float]:
        """A point beyond the target, along the line of travel."""
        (x0, y0), (x1, y1) = self.at, to
        over = self.dice.uniform(0.04, 0.12)
        return (x1 + (x1 - x0) * over, y1 + (y1 - y0) * over) if distance else to

    async def _glide(self, cdp: Any, session_id: str, to: tuple[float, float]) -> int:
        points = await motion.between_async(self.at, to)
        seconds = self.travel_time(math.dist(self.at, to)) / max(len(points), 1)
        for x, y in points:
            await cdp.send.Input.dispatchMouseEvent(
                params={"type": "mouseMoved", "x": x, "y": y}, session_id=session_id)
            await asyncio.sleep(self.draw((seconds * 0.6, seconds * 1.4)))
        self.at = to
        return len(points)

    async def reach(self, cdp: Any, session_id: str, to: tuple[float, float]) -> int:
        """Travel there, sometimes past it first. Returns how many moves were sent."""
        distance = math.dist(self.at, to)
        moves = 0
        if self._overshoots(distance):
            moves += await self._glide(cdp, session_id, self._past(to, distance))
        moves += await self._glide(cdp, session_id, to)
        await asyncio.sleep(self.draw(self.pace.dwell))
        return moves

    async def press_at(self, cdp: Any, session_id: str, to: tuple[float, float],
                       button: str = "left") -> None:
        """Press where the pointer already is. Travel first; this does not move."""
        x, y = to
        for kind in ("mousePressed", "mouseReleased"):
            await cdp.send.Input.dispatchMouseEvent(
                params={"type": kind, "x": x, "y": y, "button": button, "clickCount": 1},
                session_id=session_id)
            if kind == "mousePressed":
                await asyncio.sleep(self.draw(self.pace.press))

    async def rest(self) -> None:
        """The gap between one act and the next."""
        await asyncio.sleep(self.draw(self.pace.rest))

    async def rest_key(self) -> None:
        """The gap between one keystroke and the next. Shorter than between acts."""
        await asyncio.sleep(self.draw(self.pace.keystroke))


def _self_check() -> None:
    """M2, M3, M4, M6 need no browser. See gates/pointer-motion.md.

        uv run python -m factory.browser.hand
    """
    a, b = Hand(seed=7), Hand(seed=7)
    assert [a.draw(a.pace.dwell) for _ in range(6)] == \
           [b.draw(b.pace.dwell) for _ in range(6)], "M6 same seed, same delays"
    assert [a.aim() for _ in range(4)] == [b.aim() for _ in range(4)], "M6 same seed, same aim"

    h = Hand(seed=11)
    aims = [h.aim() for _ in range(40)]
    assert len({round(fx, 6) for fx, _ in aims}) > 30, "M3 the landing point varies"
    assert all(0.15 <= fx <= 0.85 and 0.15 <= fy <= 0.85 for fx, fy in aims), "M3 stays inside"

    near, far = h.travel_time(20), h.travel_time(900)
    assert far > near, "M4 longer moves take longer"
    assert far < near * (900 / 20), "M4 and sublinearly"

    h.at = (100.0, 300.0)
    long_moves = sum(h._overshoots(900) for _ in range(400))
    short_moves = sum(h._overshoots(20) for _ in range(400))
    assert long_moves > short_moves, "M2 long moves overshoot more often"
    assert long_moves > 0, "M2 overshoot happens at all"

    delays = [h.draw(h.pace.dwell) for _ in range(400)]
    assert len(set(delays)) > 390, "M4 timing is drawn, not constant"
    #: The defining property of a log-normal: the mean sits above the median, because the
    #: tail is on the right. A uniform draw has them equal.
    assert sum(delays) / len(delays) > sorted(delays)[len(delays) // 2], \
        "M4 the tail is right-skewed, not uniform"
    print("hand: M2 M3 M4 M6 ok")


if __name__ == "__main__":
    _self_check()
