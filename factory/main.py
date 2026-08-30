"""The composition root. The only module that knows every driver.

Drivers are built lazily and only if they can be: no key, no MODEL; no browser, no
BROWSER. Absent is a state, never a subclass that raises when used.

Nothing here decides anything. It hands each driver what the others produced, which is
the only place in the tree allowed to know that both exist.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from factory.browser import pace as pace_fitting
from factory.browser import record
from factory.browser.driver import Browser
from factory.browser.hand import Pace
from factory.core.memory import Kind, Tier
from factory.memory.driver import Memory

#: How a person drives a browser is a property of them and their computer, not of any task,
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


def _listening(port: int) -> bool:
    from factory.browser import session
    try:
        session.endpoint(port)
    except OSError:
        return False
    return True


async def demonstrate(task: str, *, port: int = 9222) -> Path:
    """Record one demonstration of a task, in the browser the factory drives.

    THE PERSON DRIVES AND NOTHING HERE ACTS. The recorder listens; every act reported is
    one they performed. That is what makes the segment admissible for induction and for
    fitting a pace, both of which forbid the factory learning from its own driving.
    """
    from factory.browser import profile, record, session
    from factory.browser.driver import Browser
    from factory.core.ledger import Act, Segment, Whose
    from factory.store import ledger

    started = None if _listening(port) else profile.launch(
        Path.home() / ".factory" / "profile", port)
    for _ in range(80):
        try:
            url = session.endpoint(port)
            break
        except OSError:
            await asyncio.sleep(0.25)
    else:
        raise RuntimeError(f"nothing answering on {port}")

    browser = await Browser.attach(url)
    seen: list[Act] = []
    await record.acts(browser._at.page, browser.cdp, seen)

    print(f"recording {task!r} -- do the task in the browser, then press Enter here.")
    await asyncio.to_thread(input)

    kept = ledger.keep(Segment(whose=Whose.PERSON, intent=task, acts=list(seen)), task)
    print(f"kept {len(seen)} acts -> {kept}")
    if started is not None:
        print("the browser stays open; close it when you are done.")
    return kept


def compile_task(task: str) -> None:
    """Induce a program from every demonstration of a task, or say what stopped one."""
    from factory.compile.induce import program
    from factory.store import ledger

    shown = ledger.shown(task)
    print(f"{len(shown)} demonstration(s) of {task!r}")
    if len(shown) < 2:
        print("two are needed to tell what varies from what is fixed; one is the "
              "degenerate case.")
    got = program(shown, task)
    if not got:
        for question in got.questions:
            print(f"  refused: {question}")
        return
    print(f"  params {got.workflow.params}")
    for step in got.workflow.steps:
        where = step.target.described() if step.target else ""
        print(f"  {'?' if step.optional else ' '}{step.doing.value:6} {where:34} "
              f"param={step.param!r}")


def main() -> int:
    """`factory` on the command line. Only what actually does something is offered."""
    import sys

    args = sys.argv[1:]
    if args[:1] == ["vendors"]:
        from factory import vendors
        return vendors.sync()

    if args[:1] == ["demonstrate"] and args[1:]:
        asyncio.run(demonstrate(" ".join(args[1:])))
        return 0

    if args[:1] == ["compile"] and args[1:]:
        compile_task(" ".join(args[1:]))
        return 0

    from factory.store import ledger
    print("factory demonstrate <task>   record one demonstration, in your own browser")
    print("factory compile <task>       induce a program from the demonstrations of it")
    print("factory vendors sync         check the manifest against the tree")
    print(f"\ndemonstrated so far: {', '.join(ledger.tasks()) or 'nothing yet'}")
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
