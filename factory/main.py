"""The composition root. The only module that knows every driver.

Drivers are built lazily and only if they can be: no key, no MODEL; no browser, no
BROWSER. Absent is a state, never a subclass that raises when used.

Nothing here decides anything. It hands each driver what the others produced, which is
the only place in the tree allowed to know that both exist.
"""

from __future__ import annotations

import asyncio
import csv
from pathlib import Path
from typing import Any

from factory.browser import pace as pace_fitting
from factory.browser import record
from factory.browser.driver import Browser
from factory.browser.hand import Pace
from factory.core.contract import Verdict
from factory.core.memory import Kind, Tier
from factory.core.question import Question
from factory.memory.driver import Memory
from factory.store.ledger import HOME

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
    fitted = pace_fitting.fit(await browser.watched(),
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


async def attached(port: int) -> tuple[Any, Any]:
    """The person's own browser, launched if it is not already there, then attached.

    ONE ARRIVAL FOR EVERY COMMAND. Recording and running want the same browser on the same
    profile -- a second copy of this is a second set of flags and a second answer to "is it
    already open", and the two would drift the first time one of them learned something.
    """
    from factory.browser import profile, session
    from factory.browser.driver import Browser

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
    return await Browser.attach(url, pace=remembered_pace(store())), started


def store() -> Memory:
    """What is known, kept where the ledger is. One store, not one per command."""
    return Memory(at=HOME / "memory.db")


def rows_of(path: str | None) -> list[dict[str, str]]:
    """The rows to run over. No file is one row: a workflow with no parameters runs once."""
    if not path:
        return [{}]
    with open(path, newline="", encoding="utf-8") as opened:
        return [{k: v or "" for k, v in row.items() if k} for row in csv.DictReader(opened)]


def _typed(question: Question) -> str | None:
    """Ask the person at the keyboard. Nobody there is an answer too."""
    print(f"\n  ? {question.about}\n    {question.because}")
    if question.candidates:
        print(f"    seen: {', '.join(question.candidates[:8])}")
    try:
        return input("    > ").strip() or None
    except EOFError:
        return None


def allowed(memory: Memory, workflow: Any, authority: Any) -> int:
    """Get consent for every step that cannot be shown to be undoable, before anything runs.

    ASKED ONCE PER STEP, NOT ONCE PER ROW. A permit is held at workflow scope with a budget,
    so a person answers for a step and every later row and later run spends against that
    answer rather than asking again.

    WHY EVERY UNPROVEN STEP AND NOT A LIST OF RISKY ONES. `compile/induce.consequential`
    can show a step reversible and cannot show one irreversible: a send whose response no
    reader could address and a click that only moved focus are the same evidence. So the
    compiler asks about both, a person separates them once, and the answer is kept.
    """
    from factory.authority import permit as permits

    granted = 0
    for step in workflow.steps:
        if not step.irreversible or permits.held(memory, step, workflow.name):
            continue
        said = authority.ask(permits.asked_for(step, workflow.name))
        if said is None:
            continue
        times = int(said) if said.isdigit() else 0
        if times:
            permits.grant(memory, step, workflow.name, times=times)
            granted += 1
    return granted


def reading(memory: Memory, workflow: str) -> dict[str, tuple[str, ...]]:
    """Where this workflow's destinations have been seen to keep the fields it binds."""
    entry = memory.recall(Kind.READING, workflow, workflow=workflow)
    return {field: tuple(path) for field, path in (entry.value or {}).items()} if entry \
        else {}


def taught(memory: Memory, workflow: str, done: Any) -> int:
    """Learn where the fields nobody could read were actually sitting. Returns how many.

    ONLY FROM AN ACT THAT WAS NOT CHECKED. A confirmed act taught nothing anybody needed --
    a reader already saw it -- and a refuted one is a destination disagreeing, which says
    nothing about where to look. What is left is exactly the demand `witness/coverage.py`
    counts, which is the point: the number it reports is the work this closes.

    WORKFLOW SCOPE, LIKE ANY OTHER EARNED THING. A path is a claim about a destination this
    workflow uses. `memory/promote.py` widens it on receipts if it keeps being right, and
    `demote` drops it when it stops -- so nothing here has to decide how much to trust it.
    """
    from factory.witness import learn

    known = reading(memory, workflow)
    found = dict(known)
    for row in done.rows:
        for step in row.steps:
            if step.contract is None or step.receipt is None:
                continue
            if step.receipt.verdict is not Verdict.UNVERIFIABLE:
                continue
            found = learn.merged(found, learn.mapping(step.contract, step.did))
    if found == known:
        return 0
    memory.remember(Kind.READING, workflow, {f: list(p) for f, p in found.items()},
                    tier=Tier.WORKFLOW, scope=workflow)
    return len(found) - len(known)


async def run_task(task: str, rows_path: str | None = None, *, port: int = 9222) -> int:
    """Compile what was demonstrated and do it, over rows, checked.

    EVERY DRIVER IS OPTIONAL AND NONE IS A STUB. With no reader admitted the ladder still
    answers -- UNVERIFIABLE -- and with nobody at the keyboard a question is recorded and
    the row refuses. Absent is a state.
    """
    from factory.authority import wheel
    from factory.authority.question import Authority
    from factory.compile.induce import program
    from factory.model.driver import MODELS, chooser
    from factory.orchestrate import driver as orchestrating
    from factory.orchestrate import lease as leases
    from factory.run import harness
    from factory.store import ledger, runs
    from factory.witness.ladder import Ladder
    from factory.witness.readers import discover
    from factory.witness.readers.mapped import Mapped

    shown = ledger.shown(task)
    if not shown:
        print(f"nothing demonstrated for {task!r}. `factory demonstrate {task}` first.")
        return 1
    got = program(shown, task)
    if not got:
        for question in got.questions:
            print(f"  refused: {question}")
        return 1

    rows = rows_of(rows_path)
    memory = store()
    authority = Authority(memory._db, asks=_typed)
    print(f"{task!r}: {len(got.workflow.steps)} steps over {len(rows)} row(s)")
    print(f"  {allowed(memory, got.workflow, authority)} permit(s) granted now")

    #: READ BEFORE THE RUN IS KEPT, so "cheaper than the first" never compares a run to
    #: itself on the day it is the only one.
    before = runs.of(task)

    #: THE LADDER IS BUILT, NOT DISCOVERED. `readers/__init__` finds the hand-written
    #: ones; a learned reader is nothing without what it learned, so the composition root
    #: is where the two meet. That seam is why the socket needs no back door cut in it.
    ladder = Ladder([*discover(), Mapped(reading(memory, task))])
    choosing = chooser()
    print(f"  model {MODELS[0] if choosing else 'none -- ambiguity becomes a question'}")

    held = orchestrating.claim(memory, memory._db, task)
    browser, _ = await attached(port)
    ours: list[Any] = []
    closing = await browser.watch(ours)
    try:
        done = await harness.over(browser, got.workflow, rows, witness=ladder,
                                  memory=memory, authority=authority, run_id=task,
                                  chooser=choosing)
    finally:
        await browser.close()

    ledger.keep(wheel.drove(ours, task, await closing()), task)
    orchestrating.ran(memory, task)
    if held is not None:
        leases.drop(memory._db, held)
    runs.keep(done, task)
    fresh = taught(memory, task, done)
    if fresh:
        print(f"  learned where {fresh} field(s) live; the next run can check them")
    return report(done, before[0] if before else None)


async def manufacture(task: str, rows_path: str | None = None, *, port: int = 9222) -> int:
    """Do it once, then decide whether it is worth having as a tool.

    THE CALL SITE `capability/driver.py` WAS MISSING. Six gates each had an eval and no
    caller; a candidate that passes five and is admitted anyway is what a pile of gates
    produces. This is the pile made into a decision.

    WHY THIS IS NOT PART OF `run`. Manufacturing spawns a second interpreter and opens a
    door onto the page. A run should cost a run.
    """
    import socket

    from factory.browser import serve
    from factory.capability.driver import Capabilities, Observed
    from factory.compile.induce import program
    from factory.kernel.driver import Door, Kernel
    from factory.run import harness
    from factory.store import ledger
    from factory.witness.ladder import Ladder
    from factory.witness.readers import discover
    from factory.witness.readers.mapped import Mapped

    shown = ledger.shown(task)
    got = program(shown, task) if shown else None
    if not got:
        print(f"nothing to manufacture from for {task!r}. `factory compile {task}` first.")
        return 1

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        door_port = int(probe.getsockname()[1])

    rows = rows_of(rows_path)
    memory = store()
    #: THE SAME LADDER A RUN GETS. A capability proved against readers that cannot address
    #: this destination comes back UNPROVEN -- which is honest, and wrong here, because the
    #: gap was closed by an earlier run and nobody told the prover.
    ladder = Ladder([*discover(), Mapped(reading(memory, task))])
    browser, _ = await attached(port)
    door = asyncio.create_task(serve.serve(browser, door_port))
    try:
        await asyncio.sleep(1.5)
        done = await harness.over(browser, got.workflow, rows, witness=ladder,
                                  memory=memory, run_id=task)
        module = got.workflow.name.replace("-", "_")

        async with await Kernel.start(
                Door(name="browser", url=f"http://127.0.0.1:{door_port}/mcp")) as kernel:

            async def watch(arguments: str) -> Observed:
                """One run of the capability, reported both ways.

                THE REAL DOOR DOES NOT RECORD WHAT IT WAS ASKED, so `sent` is derived from
                what came back: every `Did` echoes its own argument -- the text written, the
                url gone to. That is weaker than an independent record, and it is weaker in
                a knowable direction: a destination that answered identically to everything
                would read as a capability ignoring its arguments. Worth a door that reports
                its requests; not worth pretending this is that.
                """
                import ast
                cell = await kernel.run(f"await {module}.run({arguments})", timeout=120)
                acts = ast.literal_eval(cell.result) if cell.result else []
                return Observed(sent=acts, returned=acts)

            last = got.workflow.steps[-1] if got.workflow.steps else None
            answer = await Capabilities(kernel, Path.home() / ".factory" / "skills").consider(
                got.workflow, done, watch=watch, witness=ladder,
                contract=last.contract if last else None,
                inputs=tuple(f"{v!r}" for v in (rows[0].get(p, "") for p in got.workflow.params))
                if got.workflow.params else ("", ""))
    finally:
        door.cancel()
        await browser.close()

    print(f"  {answer.line()}")
    print(f"  gates passed: {' -> '.join(answer.passed) or 'none'}")
    return 0 if answer else 1


def report(done: Any, first: Any = None) -> int:
    """What the run cost, what it could show for it, and what it could not check.

    THE SECOND NUMBER, AND IT IS A COMPARISON. Against the FIRST run of this task, not the
    previous one: run to run is noise, and the claim is that the path gets cheaper as
    evidence accumulates. `observe.cheaper` answers None when either end cannot say, which
    is reported as unknown rather than rounded to no.
    """
    from factory.observe import cheaper, spent
    from factory.witness import coverage as coverages

    money = spent(done)
    seen = coverages.tally((step.did, step.receipt)
                           for row in done.rows for step in row.steps if step.receipt)
    print(f"\n  {len(done.rows)} row(s), {money.steps} step(s)")
    print(f"  confirmed {money.confirmed}  refuted {money.refuted}  "
          f"unverifiable {money.unverifiable}")
    print(f"  by rung {money.by_rung or '-'}")
    if first is not None:
        was = spent(first)
        answer = cheaper(was, money)
        said = {True: "cheaper", False: "not cheaper", None: "unknown"}[answer]
        print(f"  against the first run of this task: {said}")
    for row in done.rows:
        if row.refused:
            print(f"  refused: {row.refused.about} -- {row.refused.because}")
    worst = seen.worst()
    if worst is not None:
        print(f"\n  the reader worth building first: {worst.blocked} "
              f"({worst.acts} act(s), offering {', '.join(worst.offered) or 'nothing'})")
    return 1 if money.refuted else 0


async def demonstrate(task: str, *, port: int = 9222) -> Path:
    """Record one demonstration of a task, in the browser the factory drives.

    THE PERSON DRIVES AND NOTHING HERE ACTS. The recorder listens; every act reported is
    one they performed. That is what makes the segment admissible for induction and for
    fitting a pace, both of which forbid the factory learning from its own driving.
    """
    from factory.core.ledger import Act, Segment, Whose
    from factory.store import ledger

    browser, started = await attached(port)
    seen: list[Act] = []
    close = await browser.watch(seen)

    print(f"recording {task!r} -- do the task in the browser, then press Enter here.")
    await asyncio.to_thread(input)

    #: CLOSED BEFORE IT IS KEPT. The last act's effect arrives after it, so a segment
    #: stored without this is one whose final save can never be checked.
    after = await close()
    kept = ledger.keep(
        Segment(whose=Whose.PERSON, intent=task, acts=list(seen), after=after), task)
    print(f"kept {len(seen)} acts, {sum(len(a.saw) for a in seen) + len(after)} "
          f"exchanges -> {kept}")
    if started is not None:
        print("the browser stays open; close it when you are done.")
    return kept


def compile_task(task: str) -> None:
    """Induce a program from every demonstration of a task, or say what stopped one."""
    from factory.compile.induce import findable, program
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
        checked = ", ".join(step.contract.expects) if step.contract else "-"
        alone = findable(step, shown)
        print(f"  {'?' if step.optional else ' '}{step.doing.value:6} {where:34} "
              f"param={step.param!r:12} checks={checked}"
              f"{'' if alone else '   AMBIGUOUS ON ITS OWN PAGE'}")

    #: THE SECOND NUMBER, BEFORE ANYTHING RUNS. A step with no contract is a step whose
    #: verdict can only be UNVERIFIABLE, and knowing that from the compiler is what makes
    #: `witness/coverage` a demand signal rather than a post-mortem.
    told = sum(1 for step in got.workflow.steps if step.contract)
    lost = [s for s in got.workflow.steps if not findable(s, shown)]
    print(f"\n  {told} of {len(got.workflow.steps)} steps can be checked at all")
    if lost:
        print(f"  {len(lost)} step(s) named a control that shares its role and name with a "
              f"sibling. `locate` refuses on two matches, so these will not run as recorded "
              f"-- the page has to be told which one, and that is a question, not a guess.")
    if not told:
        print("  nothing here is checkable: the demonstration recorded no traffic, so "
              "every verdict would be unverifiable.")


def noticed() -> int:
    """What the ledger corroborates, and what it does not yet.

    THE CALL SITE `capability/notice.py` WAS MISSING. Corroboration across sittings decided
    nothing while nothing asked it: a rule with no reader is a rule nobody follows.

    A task shown ten times in one afternoon is one experiment and is reported as such --
    that is the whole point, and seeing it said out loud is what stops somebody compiling
    it anyway.
    """
    from factory.capability import notice
    from factory.store import ledger

    every = ledger.tasks()
    if not every:
        print("nothing demonstrated yet. `factory demonstrate <task>` records one.")
        return 0

    ready = {n.task for n in notice.worth_compiling()}
    for task in every:
        seen = notice.across(task, ledger.shown(task))
        mark = "ready" if seen else "  -  "
        print(f"  {mark}  {task:28} {seen.why()}")
    print(f"\n{len(ready)} of {len(every)} worth compiling. Corroboration is across "
          f"sittings, not repetitions: {notice.ENOUGH} sittings, {notice.SITTING} apart.")
    return 0


def due_now() -> int:
    from factory.orchestrate import driver as orchestrating
    from factory.orchestrate.maintain import sweep

    memory = store()
    standing = orchestrating.waiting(memory, memory._db)
    if not standing:
        print("no workflow has a cadence yet.")
    for owed in standing:
        why = ("" if owed.startable else
               f"  ({'held by ' + owed.held_by if owed.held_by else 'nobody allowed it'})")
        print(f"  {owed.cadence.workflow:24} owes {owed.runs}{why}")
    print(f"\n  {sweep(memory).said()}")
    return 0


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

    if args[:1] == ["notice"]:
        return noticed()

    if args[:1] == ["compile"] and args[1:]:
        compile_task(" ".join(args[1:]))
        return 0

    if args[:1] == ["manufacture"] and args[1:]:
        rows = args[-1] if len(args) > 2 and args[-1].endswith(".csv") else None
        named = args[1:-1] if rows else args[1:]
        return asyncio.run(manufacture(" ".join(named), rows))

    if args[:1] == ["due"]:
        return due_now()

    if args[:1] == ["run"] and args[1:]:
        #: A trailing path is the rows; everything before it names the task.
        rows = args[-1] if len(args) > 2 and args[-1].endswith(".csv") else None
        named = args[1:-1] if rows else args[1:]
        return asyncio.run(run_task(" ".join(named), rows))

    from factory.store import ledger
    print("factory demonstrate <task>   record one demonstration, in your own browser")
    print("factory notice               what the ledger corroborates, and what it does not")
    print("factory compile <task>       induce a program from the demonstrations of it")
    print("factory run <task> [rows.csv] do it, over rows, checked")
    print("factory manufacture <task>   run it, then judge it as a tool worth keeping")
    print("factory due                   what is owed, and what receipts moved")
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
    #: CONSENT IS ASKED ONCE PER STEP, NOT ONCE PER ROW, and a step that was shown to be
    #: undoable is never asked at all. Both directions, because a gate that asks about
    #: everything is one somebody turns off and a gate that asks about nothing is a brick.
    from factory.core.verbs import Doing
    from factory.core.workflow import Step, Target, Workflow

    asked: list[str] = []

    class Answering:
        def ask(self, question: object) -> str:
            asked.append(getattr(question, "about", ""))
            return "9"

    send = Step(doing=Doing.PRESS, intent="send it", irreversible=True,
                target=Target(role="button", name="Send"))
    save = Step(doing=Doing.PRESS, intent="save it", irreversible=False,
                target=Target(role="button", name="Save"))
    flow = Workflow(name="outreach", steps=[send, save])

    consent = Memory()
    assert allowed(consent, flow, Answering()) == 1, "one step needed consent, one did not"
    assert len(asked) == 1 and "send it" in asked[0], asked
    assert allowed(consent, flow, Answering()) == 0, "held already: nobody is asked twice"
    assert len(asked) == 1, f"asked again on a permit already held: {asked}"

    assert rows_of(None) == [{}], "no rows is one row, not none"

    #: THE SECOND NUMBER IS A COMPARISON, so it needs the run it is compared to. A run that
    #: died with its process could never be one end of it, and the claim would read as
    #: unknown forever.
    from factory.core.contract import Contract, Receipt
    from factory.core.evidence import Did, RowRun, Run, StepRun

    def ran(rung: str) -> Run:
        return Run(workflow="outreach", rows=[RowRun(row={}, steps=[StepRun(
            did=Did(ok=True), rung=rung,
            receipt=Receipt(verdict=Verdict.CONFIRMED, reader="fetched"))])])

    assert report(ran("remembered"), ran("chosen")) == 0, "a run with no refutation is 0"
    assert report(ran("chosen"), None) == 0, "with nothing to compare to it still reports"

    #: WHAT A RUN TEACHES, AND WHAT IT MUST NOT. Only an act nobody could check has
    #: anything to say about where to look: a confirmed act was already read, and a refuted
    #: one is a destination disagreeing. Learning from either would build a mapping out of
    #: answers rather than out of blindness.
    from factory.core.evidence import Exchange
    from factory.witness.learn import mapping as learned_paths

    hidden = Did(ok=True, exchanges=[Exchange(
        url="/api", status=200, content_type="application/json",
        body='{"data": {"customer": {"full_name": "Ada Lovelace"}}}')])
    wanted = Contract(expects={"name": "Ada Lovelace"})

    def outcome(verdict: Verdict) -> Run:
        return Run(workflow="outreach", rows=[RowRun(row={}, steps=[StepRun(
            did=hidden, rung="accessible", contract=wanted,
            receipt=Receipt(verdict=verdict, reader="fetched"))])])

    school = Memory()
    assert reading(school, "outreach") == {}, "nothing run, nothing known"
    assert taught(school, "outreach", outcome(Verdict.CONFIRMED)) == 0, \
        "an act a reader already saw teaches nothing"
    assert taught(school, "outreach", outcome(Verdict.REFUTED)) == 0, \
        "a destination disagreeing says nothing about where to look"

    assert taught(school, "outreach", outcome(Verdict.UNVERIFIABLE)) == 1, "blindness teaches"
    kept = reading(school, "outreach")
    assert kept == learned_paths(wanted, hidden), kept
    assert taught(school, "outreach", outcome(Verdict.UNVERIFIABLE)) == 0, \
        "the same lesson twice is one lesson"
    assert reading(school, "other workflow") == {}, "learned for one, not for all"

    print(f"main: pace fitted from {fitted.samples['keystroke']} gaps, kept at MAIN, "
          f"recalled as {tuple(round(v, 3) for v in back.keystroke)}; "
          f"consent asked {len(asked)}x for 2 steps over 2 runs; "
          f"learned {sorted(kept)} from one act nobody could check")


if __name__ == "__main__":
    _self_check()
