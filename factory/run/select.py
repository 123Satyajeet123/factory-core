"""Which mechanism answers this step, and remembering the answer so the next one is cheaper.

ORDERED BY COST, AND THEREFORE LEARNED. `witness/ladder.py` is ordered by evidence quality
and never moves; this is the other kind. What a step costs is an empirical claim about that
step on that surface, and the whole point is that it goes down.

A RESOLUTION IS EVIDENCE, NOT A CACHE. A cache would store an answer and hand it back. What
is kept here is a TARGET -- role and name, the same thing `locate` searches by -- so the
cheap path on the next run is the ordinary structural one rather than a second mechanism
with its own failure modes. It starts at EXECUTION scope and widens only on witness
receipts, like anything else in `memory/`.

NOTHING IS REMEMBERED FROM A REFUSAL. A chooser that declined, or a rung that could not see,
leaves no entry: remembering a guess is how a wrong answer becomes permanent.
"""

from __future__ import annotations

from typing import Any

from factory.browser import locate
from factory.browser.locate import Found
from factory.core.memory import Kind, Tier
from factory.core.workflow import Step, Target


def asked_about(step: Step, workflow: str) -> str:
    """What this step needs resolved, named so two steps do not share an answer."""
    wanted = step.target.described() if step.target else step.doing.value
    return f"{workflow}:{step.doing.value}:{wanted}"


async def target_for(browser: Any, step: Step, *, chooser: Any = None,
                     authority: Any = None, memory: Any = None,
                     workflow: str = "", run: str = "") -> Found:
    """Resolve this step's control as cheaply as it can be resolved today.

    A remembered resolution is tried FIRST and structurally, so it costs what any other
    structural match costs. If the page no longer agrees, the descent happens again rather
    than the run failing on an answer that used to be true.
    """
    if step.target is None:
        return Found(rung="none", why="no target recorded")

    key = asked_about(step, workflow)
    remembered = (memory.recall(Kind.TARGET, key, run=run, workflow=workflow)
                  if memory is not None else None)

    if remembered is not None:
        found = await browser.find(Target.model_validate(remembered.value))
        if found:
            return found.model_copy(update={"rung": "remembered"})
        #: R3. The page moved on. Fall through and resolve again; the stale entry is left
        #: for `memory/demote.py` to drop on the refutation that follows, rather than being
        #: deleted here on a guess about why it missed.

    found = await browser.find(step.target, chooser)

    #: THE BOTTOM RUNG. Rung 0 could not resolve it and neither could a model, so a person
    #: is asked -- once, with what the page actually offered. The answer is kept exactly as
    #: a model's would be, so the run after this one costs nothing: that is the whole reason
    #: asking is cheaper than a hardcoded answer rather than more expensive.
    if not found and found.question is not None and authority is not None:
        said = authority.ask(found.question)
        picked = next((i for i, line in found.among.items() if line == said), None)
        if picked is not None:
            every = await browser.candidates()
            if 0 <= picked < len(every):
                role, name, node = locate.reads(every[picked])
                if node is not None:
                    found = Found(backend_node_id=node, rung="asked",
                                  why=f"a person said {said!r}", among=found.among,
                                  resolved=Target(role=role, name=name))

    if found and found.rung in ("chosen", "asked") and found.resolved and memory is not None:
        #: EXECUTION scope, because one resolution is one observation. Widening it is
        #: `memory/promote.py`'s to do, on receipts.
        memory.remember(Kind.TARGET, key, found.resolved.model_dump(),
                        tier=Tier.EXECUTION, scope=run or workflow)
    return found
