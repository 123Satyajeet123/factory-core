"""The composition root. The only module that knows every driver.

Drivers are built lazily and only if they can be: no key, no MODEL; no browser, no
BROWSER. Absent is a state, never a subclass that raises when used.

Nothing here decides anything. It hands each driver what the others produced, which is
the only place in the tree allowed to know that both exist.
"""

from __future__ import annotations

from factory.browser import pace as pace_fitting
from factory.browser import record
from factory.browser.driver import Browser
from factory.browser.hand import Pace
from factory.core.memory import Kind, Tier
from factory.memory.driver import Memory

#: How a person drives a browser is a property of them and their machine, not of any task,
#: so the fit lives at MAIN under one key and every workflow uses it.
OPERATOR = "operator"


def remembered_pace(memory: Memory) -> Pace | None:
    """The operator's own rhythm, if anything has ever been fitted."""
    entry = memory.recall(Kind.PACE, OPERATOR)
    return Pace(**entry.value) if entry else None


async def driver(memory: Memory, cdp_url: str, *, seed: int | None = None) -> Browser:
    """A BROWSER driver paced by whatever has been learned about this person."""
    return await Browser.attach(cdp_url, seed=seed, pace=remembered_pace(memory))


async def learn_pace(memory: Memory, browser: Browser) -> pace_fitting.Fitted:
    """Fit what the recorder saw a PERSON do, and keep it.

    Only ever called on a demonstration. Fitting to the factory's own driving would have
    the distribution converge on whatever we already do -- see gates/learned-pace.md.
    """
    fitted = pace_fitting.fit(await record.drain(browser._at.page),
                              over=remembered_pace(memory))
    memory.remember(Kind.PACE, OPERATOR, fitted.pace.model_dump(), tier=Tier.MAIN)
    return fitted


def main() -> int:
    """`factory` on the command line. Nothing is wired to it yet."""
    print("factory: drivers exist, no workflow runs yet. See gates/ for what is settled.")
    return 0


def _self_check() -> None:
    """The round trip: fit, keep, and come back paced. No browser.

        uv run python -m factory.main
    """
    import math
    import random

    dice = random.Random(9)
    keys, at = [], 0.0
    for _ in range(200):
        at += dice.lognormvariate(math.log(310), 0.25)
        keys.append(at)
    watched = record.Watched(keys=keys)

    memory = Memory()
    assert remembered_pace(memory) is None, "nothing fitted, nothing remembered"

    fitted = pace_fitting.fit(watched)
    memory.remember(Kind.PACE, OPERATOR, fitted.pace.model_dump(), tier=Tier.MAIN)

    back = remembered_pace(memory)
    assert back is not None and back.keystroke == fitted.pace.keystroke, "it came back"
    assert back.keystroke != Pace().keystroke, "and it is not the default"
    print(f"main: pace fitted from {fitted.samples['keystroke']} gaps, kept at MAIN, "
          f"recalled as {tuple(round(v, 3) for v in back.keystroke)}")


if __name__ == "__main__":
    _self_check()
