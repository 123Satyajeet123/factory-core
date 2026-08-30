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
    if step.surface and not await browser.on(step.surface):
        return Did(ok=False, delivery=Delivery.NOT_PROBED,
                   detail=f"no single tab showing {step.surface}")
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


def supplied(workflow: Workflow, row: Mapping[str, str],
             authority: Any = None) -> tuple[dict[str, str], Question | None]:
    """The row as the workflow needs to read it, or the question standing in the way.

    A parameter no column is named for is not a broken row. It is the one thing nobody has
    decided: which column supplies it. Asked per parameter, so the answer is reusable --
    keyed on `<workflow>.<param>`, a person answers once and every later row of every later
    run reads the same column without asking.

    With no authority, or with nobody answering, the question comes back and the caller
    refuses. That is what it would have done anyway, and now the reason is answerable.
    """
    missing = workflow.missing_from(row)
    if not missing:
        return dict(row), None

    reading = dict(row)
    for param in missing:
        question = Question(
            kind=Ask.PARAM, about=f"{workflow.name}.{param}",
            because=f"no column of the row is named {param}",
            candidates=tuple(sorted(row)))
        column = authority.ask(question) if authority is not None else None
        if not column or column not in row:
            return reading, question
        reading[param] = row[column]
    return reading, None


async def over(browser: Any, workflow: Workflow, rows: Sequence[Mapping[str, str]],
               *, witness: Any = None, authority: Any = None) -> Run:
    """The whole workflow, over every row. Stops a row at its first failing step."""
    run = Run(workflow=workflow.name)

    for index, row in enumerate(rows):
        if index:
            #: Every act inside a row is paced; the rows themselves were not, so a hundred
            #: of them arrived at the pace of a single act however human each one looked.
            await browser.next_row()
        reading, refused = supplied(workflow, row, authority)
        if refused is not None:
            run.rows.append(RowRun(row=dict(row), refused=refused))
            continue
        row = reading

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
