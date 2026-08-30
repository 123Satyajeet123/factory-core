"""Fitting a Pace to the person, from what the recorder saw them do.

FOR THE FACTORY, NOT FOR A WORKFLOW. How someone drives a browser is a property of them and
their computer, not of the task in front of them, so a fit is held at operator scope and
every workflow uses it.

THE SAME PRINCIPLE THE FACTORY RUNS ON. A capability comes from the record rather than from
an idea about what the procedure might be. A rhythm comes from the record too, rather than
from constants somebody picked -- and the constants in `Pace` were picked by me.

WHAT IS FITTED AND WHAT IS NOT. The distributions are fitted; the curve is not. Path
geometry is ghost-cursor's and stays measured rather than learned, because a person's
recorded pointer path is sampled at the browser's event rate and is not the same object as
a generated path.
"""

from __future__ import annotations

import itertools
import math
import statistics
from typing import Any

from pydantic import BaseModel, Field

from factory.browser.hand import Pace
from factory.browser.record import Watched

#: Below this many observations a parameter keeps its default. Fitting noise is worse than
#: not fitting, because it looks like knowledge.
ENOUGH = 12
#: A gap this long ends one pointer movement and starts the next.
BURST_GAP_MS = 180.0


class Fitted(BaseModel):
    """A pace, and the evidence behind each part of it.

    `samples` is not bookkeeping. A fit from twelve observations and one from twelve
    hundred are different claims, and promotion has to be able to tell them apart.
    """

    pace: Pace = Field(default_factory=Pace)
    samples: dict[str, int] = Field(default_factory=dict)
    kept_default: tuple[str, ...] = Field(default_factory=tuple)


def _span(values: list[float]) -> tuple[float, float] | None:
    """The middle half, in seconds. `Hand.draw` treats the midpoint as its median."""
    if len(values) < ENOUGH:
        return None
    ordered = sorted(values)
    low = ordered[len(ordered) // 4] / 1000
    high = ordered[(3 * len(ordered)) // 4] / 1000
    return (low, high) if high > low > 0 else None


def _gaps(times: list[float], ceiling: float = 4000.0) -> list[float]:
    """Intervals between consecutive events, with pauses for thought dropped."""
    return [b - a for a, b in itertools.pairwise(times) if 0 < b - a < ceiling]


def _bursts(moves: list[tuple[float, float, float]]) -> list[tuple[float, float]]:
    """One movement each: how far it went and how long it took."""
    out, run = [], [moves[0]] if moves else []
    for point in moves[1:]:
        if point[2] - run[-1][2] > BURST_GAP_MS:
            out.append(run)
            run = []
        run.append(point)
    out.append(run)
    return [(math.dist(b[0][:2], b[-1][:2]), b[-1][2] - b[0][2])
            for b in out if len(b) > 2 and math.dist(b[0][:2], b[-1][:2]) > 8]


def _fitts(bursts: list[tuple[float, float]], width: float) -> tuple[float, float] | None:
    """Least squares on time = base + scale * log2(1 + distance / width). Seconds."""
    if len(bursts) < ENOUGH:
        return None
    xs = [math.log2(1 + distance / width) for distance, _ in bursts]
    ys = [ms / 1000 for _, ms in bursts]
    mean_x, mean_y = statistics.fmean(xs), statistics.fmean(ys)
    spread = sum((x - mean_x) ** 2 for x in xs)
    if spread <= 0:
        return None
    scale = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True)) / spread
    base = mean_y - scale * mean_x
    return (base, scale) if base > 0 and scale > 0 else None


def _paired(presses: list[tuple[float, Any, Any]], releases: list[float]) -> list[float]:
    """How long a button was held. Each press takes the first release after it."""
    held, remaining = [], sorted(releases)
    for when, *_ in sorted(presses):
        after = [r for r in remaining if r >= when]
        if after:
            held.append(after[0] - when)
            remaining.remove(after[0])
    return held


def _before_press(watched: Watched) -> list[float]:
    """The pause between arriving somewhere and pressing it."""
    moves = sorted(m[2] for m in watched.moves)
    out = []
    for when, *_ in watched.presses:
        earlier = [m for m in moves if m <= when]
        if earlier:
            out.append(when - earlier[-1])
    return out


def fit(watched: Watched, over: Pace | None = None) -> Fitted:
    """A Pace fitted where there is evidence, and left alone where there is not."""
    pace = (over or Pace()).model_copy(deep=True)
    samples: dict[str, int] = {}
    defaulted: list[str] = []

    for name, values in (("keystroke", _gaps(watched.keys)),
                         ("press", _paired(watched.presses, watched.releases)),
                         ("rest", _gaps(sorted(watched.releases))),
                         ("dwell", _before_press(watched))):
        samples[name] = len(values)
        span = _span(values)
        if span:
            setattr(pace, name, span)
        else:
            defaulted.append(name)

    aims = [v for _, fx, fy in watched.presses for v in (fx, fy) if v is not None]
    samples["aim_spread"] = len(aims)
    if len(aims) >= ENOUGH:
        pace.aim_spread = max(0.02, statistics.stdev(aims))
    else:
        defaulted.append("aim_spread")

    bursts = _bursts(watched.moves)
    samples["travel"] = len(bursts)
    fitted = _fitts(bursts, pace.travel_width)
    if fitted:
        pace.travel_base, pace.travel_scale = fitted
    else:
        defaulted.append("travel")

    return Fitted(pace=pace, samples=samples, kept_default=tuple(defaulted))


def _self_check() -> None:
    """P1, P3, P6 need no browser.

        uv run python -m factory.browser.pace
    """
    import random

    dice = random.Random(5)
    thin = Watched(keys=[float(i) * 100 for i in range(4)])
    poor = fit(thin)
    assert poor.pace.keystroke == Pace().keystroke, "P3 too few samples keeps the default"
    assert "keystroke" in poor.kept_default and poor.samples["keystroke"] == 3

    #: A person who types slowly, holds the button a long time, and lands off centre.
    keys, at = [], 0.0
    for _ in range(200):
        at += dice.lognormvariate(math.log(320), 0.25)
        keys.append(at)
    presses = [(float(i) * 900, 0.5 + dice.gauss(0, 0.30), 0.5 + dice.gauss(0, 0.30))
               for i in range(60)]
    releases = [when + dice.uniform(180, 260) for when, _, _ in presses]
    rich = fit(Watched(keys=keys, presses=presses, releases=releases))

    lo, hi = rich.pace.keystroke
    assert 0.20 < (lo + hi) / 2 < 0.45, f"P1 keystroke fitted from events: {(lo, hi)}"
    assert rich.pace.keystroke != Pace().keystroke, "P1 the default was replaced"
    held_lo, held_hi = rich.pace.press
    assert 0.15 < (held_lo + held_hi) / 2 < 0.30, f"P1 hold fitted: {(held_lo, held_hi)}"
    assert rich.pace.aim_spread > Pace().aim_spread, "P1 a wider aim than the default"
    assert isinstance(rich.pace, Pace), "P6 the output is a Pace"
    assert rich.samples["aim_spread"] == 120

    #: P4: a key event is a timestamp and nothing else. If this ever holds a string, the
    #: recorder has started keeping what was typed.
    assert all(isinstance(when, float) for when in rich.samples and keys), \
        "P4 key events carry timing, never content"
    print("pace:", {k: v for k, v in rich.samples.items()},
          "defaulted:", rich.kept_default)
    print("pace: P1 P3 P6 ok")


if __name__ == "__main__":
    _self_check()
