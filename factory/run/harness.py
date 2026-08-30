"""Execute a workflow over its rows.

WHAT THIS IS NOT. It decides nothing about how to do a step -- which control, which
mechanism, whether to retry -- because those are `run/select.py`, `browser/locate.py` and
`run/retry.py`. This walks rows and steps, and hands each one to the thing that owns it.

A ROW THAT CANNOT START IS NOT A ROW THAT FAILED. A workflow's parameters come from
induction, so a row missing one is a row nobody has decided about: it produces a question,
which is answerable, rather than a failure, which is only countable.

WITNESSING IS PER STEP AND INDEPENDENT OF HOW THE STEP WAS DONE. A step with no contract
comes back unverifiable, and that is `witness/coverage.py`'s to count -- not something to
paper over by treating a successful dispatch as evidence.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from factory.core.evidence import Delivery, Did, RowRun, Run, StepRun
from factory.core.question import Ask, Question
from factory.core.verbs import Doing
from factory.core.workflow import Step, Workflow


async def one_step(browser: Any, step: Step, row: Mapping[str, str]) -> Did:
    """Do one step, on one row. The driver owns the guard, the hand and the reading."""
    if step.doing is Doing.GO:
        return await browser.go(step.wants(row) or step.value)

    if step.target is None:
        return Did(ok=False, delivery=Delivery.NOT_PROBED, detail="no target recorded")

    if step.doing is Doing.PRESS:
        return await browser.click(step.target)

    found = await browser.find(step.target)
    if not found:
        return Did(ok=False, delivery=Delivery.NOT_PROBED, detail=found.why)
    pressed = await browser.press(found)
    if not pressed.ok:
        return pressed
    await browser.clear()
    return await browser.type(step.wants(row))


async def over(browser: Any, workflow: Workflow, rows: Sequence[Mapping[str, str]],
               *, witness: Any = None) -> Run:
    """The whole workflow, over every row. Stops a row at its first failing step."""
    run = Run(workflow=workflow.name)

    for row in rows:
        missing = workflow.missing_from(row)
        if missing:
            run.rows.append(RowRun(row=dict(row), refused=Question(
                kind=Ask.TARGET, about=workflow.name,
                because=f"the row supplies no {', '.join(missing)}",
                candidates=tuple(sorted(row)))))
            continue

        done = RowRun(row=dict(row))
        for step in workflow.steps:
            #: A guarded step runs when its control is there and is skipped when it is not.
            #: Failing the row on an absent optional control would fail every row that is
            #: normal, which is the majority of them.
            if step.optional and step.target is not None and not await browser.find(step.target):
                continue
            did = await one_step(browser, step, row)
            receipt = None
            if step.contract is not None and witness is not None:
                #: Bound to THIS row. A contract carrying the demonstration's value would
                #: confirm every row against the record the demonstration wrote.
                receipt = witness.witness(did, step.contract.for_row(row))
            done.steps.append(StepRun(intent=step.intent, did=did, receipt=receipt))
            if not did.ok:
                break
        run.rows.append(done)

    return run
