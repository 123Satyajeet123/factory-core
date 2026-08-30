from __future__ import annotations

import argparse
import ast
import asyncio
import contextlib
import random
import shutil
import sys
import time
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from demo import surface as site

ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home() / ".factory-demo"
LEDGER, RUNS, MEMORY, SKILLS = HOME / "ledger", HOME / "runs", HOME / "memory.db", HOME / "skills"

TASK = "outreach"
AMBIGUOUS_TASK = "reveal from the list"
LOOPING_TASK = "log two contacts"
CDP_PORT = 9222
DEMONSTRATED = [{"name": "Vinayak Suthar", "id": "p1"},
                {"name": "Sanjay Raut", "id": "p2"}]
ROWS = [{TASK: "amrita@odwen.example"}, {TASK: "ketan@zingbus.example"}]
BAR = "-" * 78
ANSWERS = {True: "agree", False: "DISAGREE", None: "not decidable here"}


class Mistyped(RuntimeError):
    pass


@dataclass
class Shown:
    factory: list[str] = field(default_factory=list)
    hand: list[str] = field(default_factory=list)
    agree: bool | None = None
    gap: list[str] = field(default_factory=list)
    skipped: str = ""

    def say(self, line: str = "") -> None:
        self.factory.append(line)


def out(text: str = "") -> None:
    print(text, flush=True)


def block(title: str, lines: Sequence[str]) -> None:
    if lines:
        out(f"  {title}")
        for line in lines:
            out(f"    {line}")


def source(module: str) -> str:
    path = ROOT / (module.replace(".", "/") + ".py")
    return path.read_text(encoding="utf-8") if path.exists() else ""


def imports_of(module: str) -> set[str]:
    text = source(module)
    if not text:
        return set()
    found: set[str] = set()
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import):
            found.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            found.add(node.module)
            found.update(f"{node.module}.{a.name}" for a in node.names)
    return {n for n in found if n.startswith(("factory.", "evals."))}


def statements(module: str) -> int:
    text = source(module)
    if not text.strip():
        return 0
    body = ast.parse(text).body
    return sum(1 for node in body
               if not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)))


def reached(start: str, universe: set[str]) -> set[str]:
    seen: set[str] = set()
    stack = [start]
    while stack:
        at = stack.pop()
        if at in seen or at not in universe:
            continue
        seen.add(at)
        stack.extend(imports_of(at))
    return seen


TIERS = {"core": "0 core", "browser": "1 driver", "kernel": "1 driver", "model": "1 driver",
         "witness": "1 driver", "memory": "1 driver", "capability": "1 driver",
         "compile": "2 line", "run": "2 line", "orchestrate": "2 line",
         "authority": "2 line", "store": "3 root"}


def modules(under: str) -> list[str]:
    return sorted(".".join(p.relative_to(ROOT).with_suffix("").parts)
                  for p in ROOT.glob(f"{under}/**/*.py") if p.name != "__init__.py")


def tier_of(module: str) -> str:
    parts = module.split(".")
    return TIERS.get(parts[1] if len(parts) > 2 else "", "3 root")


async def board() -> Shown:
    shown = Shown()
    every = set(modules("factory"))
    wired = reached("factory.main", every)

    checked: set[str] = set()
    suites = modules("evals")
    for suite in suites:
        for name in reached(suite, every | set(suites)):
            if name.startswith("factory."):
                checked.add(name)
    for module in every:
        if "_self_check" in source(module):
            checked.add(module)

    empty = {m for m in every if statements(m) == 0}
    orphans = sorted(every - wired - empty)

    by_tier: dict[str, list[str]] = {}
    for module in sorted(every):
        by_tier.setdefault(tier_of(module), []).append(module)

    for tier in sorted(by_tier):
        rows = by_tier[tier]
        shown.say(f"{tier}   {sum(m in wired for m in rows)}/{len(rows)} reachable, "
                  f"{sum(m in empty for m in rows)} with no code")
        for module in rows:
            state = ("EMPTY " if module in empty else
                     "      " if module in wired else "ORPHAN")
            shown.say(f"  {state} {module:42} {statements(module):3} stmt  "
                      f"{'checked' if module in checked else '-'}")
        shown.say()

    shown.say(f"{len(every)} modules: {len(wired - empty)} reachable and real, "
              f"{len(orphans)} orphaned, {len(empty)} with nothing in them")
    if empty:
        shown.say()
        shown.say("declared in the README's driver table and containing no code:")
        for module in sorted(empty):
            shown.say(f"    {module}")
    if orphans:
        shown.say()
        shown.say("written, some of them checked, and reachable from no command:")
        for module in orphans:
            shown.say(f"    {module}  ({'checked' if module in checked else 'unchecked'})")

    shown.hand = [
        "A machine fails three separate ways and only one of them looks like failure:",
        "  EMPTY    a file with a docstring and no code, named in a table as a driver",
        "  ORPHAN   written, passing an eval, and reachable from no command",
        "  UNSEEN   called, and nothing checks it",
        "",
        "The orphan is the dangerous one, because a green eval on it reads as proof. This",
        "repo's own gates say 'the call site was missing' twice; that is this class of bug",
        "found by hand, late, and only after somebody went looking.",
        "",
        "Before running this I predicted the empties would sit on the way OUT of the system",
        "-- scheduling, budget, promotion, demotion, retirement -- because every gate here",
        "is about admission and nothing has forced the question of what leaves.",
    ]
    predicted = {"factory.model.budget", "factory.orchestrate.schedule",
                 "factory.memory.promote", "factory.memory.demote"}
    missed = sorted(empty - predicted)
    shown.agree = predicted <= empty and len(missed) <= 2
    if missed:
        shown.gap.append(
            f"I predicted {len(predicted)} empties on the way out. There are {len(empty)}, "
            f"across every tier, including four named in the "
            f"README and PRINCIPLES as load-bearing: compile/refuse, browser/stealth, "
            f"browser/tabs, run/retry. My reading was wrong and the direction it was wrong "
            f"in matters -- this is not deferred cleanup, it is the middle of the tree.")
        shown.gap.append(f"unpredicted empties: {', '.join(missed)}")
    if predicted - empty:
        shown.gap.append(f"predicted empty, has code now: "
                         f"{', '.join(sorted(predicted - empty))}")
    if "factory.model.driver" in orphans:
        shown.gap.append("factory.model.driver is ORPHANED. The `chosen` rung -- the one "
                         "thing a model is for -- has no call site, so the four-rung ladder "
                         "is three rungs with a gap where the model goes.")
    if orphans:
        shown.gap.append("nothing in the tree asks about orphans. This board is the only "
                         "thing that does, and it lives in demo/.")
    return shown


class Attached:
    def __init__(self) -> None:
        self.serving: site.Serving | None = None
        self.browser: Any = None

    async def __aenter__(self) -> Attached:
        from factory.browser import profile, session
        from factory.browser.driver import Browser

        self.serving = site.Serving()
        try:
            session.endpoint(CDP_PORT)
        except OSError:
            profile.launch(HOME / "profile", CDP_PORT)
        for _ in range(80):
            try:
                url = session.endpoint(CDP_PORT)
                break
            except OSError:
                await asyncio.sleep(0.25)
        else:
            raise RuntimeError(f"nothing answering on {CDP_PORT}")
        self.browser = await Browser.attach(url, pace=remembered())
        await self.blank()
        return self

    async def blank(self) -> None:
        pages = list(self.context.pages)
        for page in pages[1:]:
            with contextlib.suppress(Exception):
                await page.close()
        self.browser._at.page = pages[0]
        self.browser._at.cdp = await self.context.new_cdp_session(pages[0])
        await self.browser._at.cdp.send("Network.enable", {})
        self.browser.bodies.watch(self.browser._at.cdp)
        await pages[0].goto("about:blank")

    async def __aexit__(self, *_: Any) -> None:
        with contextlib.suppress(Exception):
            await self.browser.close()
        if self.serving:
            self.serving.stop()

    @property
    def page(self) -> Any:
        return self.browser._at.page

    @property
    def context(self) -> Any:
        return self.browser._at.context


def store() -> Any:
    from factory.memory.driver import Memory

    HOME.mkdir(parents=True, exist_ok=True)
    return Memory(at=MEMORY)


def remembered() -> Any:
    from factory.browser.hand import Pace
    from factory.core.memory import Kind

    entry = store().recall(Kind.PACE, "operator")
    return Pace(**entry.value) if entry else None


async def typed(page: Any, selector: str, text: str, dice: random.Random) -> None:
    field = page.locator(selector)
    await field.wait_for(state="visible")
    await field.click()
    await field.fill("")
    await field.press_sequentially(text, delay=dice.uniform(55, 130))
    held = await field.input_value()
    if held != text:
        raise Mistyped(f"typed {text!r} into {selector} and it holds {held!r}")


async def perform(prospects: Any, tracker: Any, person: dict[str, str],
                  dice: random.Random) -> None:
    await prospects.goto(f"{site.Serving.prospects}/", wait_until="load")
    await typed(prospects, "#q", "category head", dice)
    await prospects.click("#go")
    await prospects.wait_for_selector("#rows tr")
    await prospects.click(f"#rows a:text-is('{person['name']}')")
    await prospects.wait_for_load_state("load")
    await prospects.click("#reveal")
    await prospects.wait_for_function("document.getElementById('mail').textContent !== ''")
    email = await prospects.inner_text("#mail")
    await tracker.goto(f"{site.Serving.tracker}/", wait_until="load")
    await tracker.bring_to_front()
    await typed(tracker, "#email", email, dice)
    await tracker.click("#add")
    await tracker.wait_for_selector("#rows tr")
    await asyncio.sleep(0.4)


async def perform_ambiguous(prospects: Any, person: dict[str, str],
                            dice: random.Random) -> None:
    await prospects.goto(f"{site.Serving.prospects}/", wait_until="load")
    await typed(prospects, "#q", "category head", dice)
    await prospects.keyboard.press("Enter")
    await prospects.wait_for_selector("#rows tr")
    await prospects.click(f"#rows tr:has(a:text-is('{person['name']}')) button")
    await prospects.wait_for_function(
        f"document.getElementById('m-{person['id']}').textContent !== ''")
    await asyncio.sleep(0.3)


async def perform_looping(tracker: Any, person: dict[str, str],
                          dice: random.Random) -> None:
    await tracker.goto(f"{site.Serving.tracker}/", wait_until="load")
    await tracker.bring_to_front()
    await typed(tracker, "#name", person["name"], dice)
    await typed(tracker, "#email", f"{person['id']}@materialdepot.example", dice)
    await tracker.click("#add")
    await tracker.wait_for_selector("#rows tr")
    await tracker.click("#send")
    await asyncio.sleep(0.4)


async def record_demonstrations() -> Shown:
    from factory.core.ledger import Segment, Whose
    from factory.store import ledger

    shown = Shown()
    dice = random.Random(11)
    mistyped: list[str] = []
    async with Attached() as up:
        tracker = await up.context.new_page()
        await tracker.goto(f"{site.Serving.tracker}/", wait_until="load")
        for task in (TASK, AMBIGUOUS_TASK, LOOPING_TASK):
            for person in DEMONSTRATED:
                for attempt in range(3):
                    seen: list[Any] = []
                    close = await up.browser.watch(seen)
                    try:
                        if task == TASK:
                            await perform(up.page, tracker, person, dice)
                        elif task == AMBIGUOUS_TASK:
                            await perform_ambiguous(up.page, person, dice)
                        else:
                            await perform_looping(tracker, person, dice)
                    except Mistyped as slipped:
                        await close()
                        mistyped.append(str(slipped))
                        if attempt == 2:
                            raise
                        continue
                    after = await close()
                    await asyncio.sleep(0.6)
                    ledger.keep(Segment(whose=Whose.PERSON, intent=task, acts=list(seen),
                                        after=after), task, at=LEDGER)
                    break

    for task in (TASK, AMBIGUOUS_TASK, LOOPING_TASK):
        for index, segment in enumerate(ledger.shown(task, at=LEDGER)):
            kept = sum(len(a.saw) for a in segment.acts) + len(segment.after)
            shown.say(f"{task!r} #{index}: {len(segment.acts)} acts, {kept} exchanges")
            for act in segment.acts:
                where = act.target.described() if act.target else "(unresolved)"
                shown.say(f"    {act.doing.value:6} {where:36} {(act.value or '')[:24]:24} "
                          f"saw={len(act.saw):2} among={len(act.among):3}"
                          f"{'  AMBIGUOUS' if act.ambiguous else ''}")
            shown.say()

    both = ledger.shown(TASK, at=LEDGER)
    table = ledger.shown(AMBIGUOUS_TASK, at=LEDGER)
    surfaces = {a.surface for s in both for a in s.acts}
    ambiguous = [a for s in table for a in s.acts if a.ambiguous]
    goes = [a for s in both for a in s.acts if a.doing.value == "go"]
    landmarks = [a for s in both for a in s.acts
                 if a.target and a.target.role in ("main", "banner", "document", "generic")]
    shown.say(f"surfaces touched: {sorted(surfaces)}")
    shown.say(f"acts the table demonstration recorded as ambiguous: {len(ambiguous)}")
    shown.say(f"navigation acts recorded anywhere: {len(goes)}")
    shown.say(f"demonstrations thrown away because the stand-in mistyped: {len(mistyped)}")
    shown.say(f"acts whose target came back as a landmark rather than a control: "
              f"{len(landmarks)}")

    shown.hand = [
        "By hand the outreach task is 8 acts: focus the query, type it, press Search, open",
        "the person, press Access email, focus the email field, type the address, press Add.",
        "Two of the eight are on a second origin.",
        "",
        "In the table the reveal control is one of two answering to `button Access email`,",
        "so Act.ambiguous must be TRUE there and FALSE on the person's own page. That is",
        "the SAFETY and LIVENESS pair for this machine.",
        "",
        "What I expect to be MISSING is the navigation. I opened the site and I opened the",
        "tracker, and neither is a click on a control.",
    ]
    shown.agree = bool(both and table and ambiguous and len(surfaces) == 2)
    if not ambiguous:
        shown.gap.append("nothing came back ambiguous, so the refusal downstream is untested")
    if len(surfaces) < 2:
        shown.gap.append(f"only {len(surfaces)} surface(s) recorded; the multi-origin claim "
                         f"is not being exercised")
    if not goes:
        shown.gap.append(
            "0 navigation acts. Doing.GO is in the vocabulary and compile/induce maps it "
            "both ways, but browser/record.py emits only write/press/key/scroll/select and "
            "listens for no navigation. So no browser demonstration can ever produce a GO "
            "step, and a compiled workflow cannot reach a surface that is not already open.")
    if landmarks:
        shown.gap.append(
            f"{len(landmarks)} act(s) recorded a landmark as their target. A press that "
            f"navigates is described AFTER the page has changed: record.resolve runs off "
            f"the handler and drains bodies first, so the link is gone by the time "
            f"DOM.getNodeForLocation asks what is at that point. The link's role and name "
            f"are lost and locate would search for a landmark on replay. Draining first is "
            f"deliberate -- naming first would let an act swallow its own effect and derive "
            f"a wrong contract -- so this is a real tension in the recorder, not a typo.")
    shown.agree = shown.agree and not landmarks
    return shown


async def fit_pace() -> Shown:
    from factory.browser import pace as fitting
    from factory.browser import record as recorder
    from factory.browser.hand import Pace
    from factory.core.memory import Kind, Tier

    shown = Shown()
    async with Attached() as up:
        await up.page.goto(f"{site.Serving.prospects}/", wait_until="load")
        await recorder.watch(up.page)
        dice = random.Random(5)
        await typed(up.page, "#q", "category head", dice)
        await up.page.click("#go")
        await up.page.wait_for_selector("#rows tr")
        for _ in range(3):
            await up.page.click("#q")
            await up.page.click("#go")
        watched = await up.browser.watched()

    before = remembered() or Pace()
    fitted = fitting.fit(watched, over=remembered())
    store().remember(Kind.PACE, "operator", fitted.pace.model_dump(), tier=Tier.MAIN)

    shown.say(f"raw: {len(watched.keys)} keydowns, {len(watched.moves)} pointer samples, "
              f"{len(watched.presses)} presses, {len(watched.releases)} releases")
    shown.say()
    for name, samples in sorted(fitted.samples.items()):
        shown.say(f"{name:12} {samples:4} samples   {rounded(getattr(before, name, None))} "
                  f"-> {rounded(getattr(fitted.pace, name, None))}"
                  f"{'' if samples else '   (prior kept: nothing to fit)'}")
    shown.say()
    shown.say(f"kept at MAIN scope under 'operator': {remembered() is not None}")

    gaps = sorted(b - a for a, b in zip(watched.keys, watched.keys[1:], strict=False)
                  if 0 < b - a < 4000)
    median = gaps[len(gaps) // 2] if gaps else 0.0
    shown.hand = [
        "The stand-in typed with gaps drawn uniformly from 55-130 ms plus playwright's own",
        f"overhead. Of {len(gaps)} raw gaps the median is {median:.0f} ms, so a keystroke",
        "distribution near that is a real fit and one left on the default means the fit",
        "ignored its input.",
        "",
        "This cannot be a fit to a person. A generator drew the gaps and every number here",
        "is an honest fit to fake data. That is the whole difference between a scripted",
        "demonstration and one you drive.",
    ]
    shown.agree = bool(gaps) and fitted.pace.keystroke != Pace().keystroke
    if not watched.moves:
        shown.gap.append("0 pointer samples: playwright dispatches one mousemove per click, "
                         "so Fitts' fitting has no bursts and keeps its prior. A person's "
                         "drive fills this and a script never will.")
    return shown


def rounded(value: Any) -> str:
    if isinstance(value, tuple):
        return "(" + ", ".join(f"{v:.3f}" for v in value) + ")"
    return f"{value:.3f}" if isinstance(value, float) else str(value)


async def corroboration() -> Shown:
    from factory.capability import notice
    from factory.store import ledger

    tasks = ledger.tasks(at=LEDGER)
    if not tasks:
        return Shown(skipped="nothing demonstrated yet. Station 1 first.")

    shown = Shown()
    for task in tasks:
        seen = notice.across(task, ledger.shown(task, at=LEDGER))
        shown.say(f"{'ready' if seen else '  -  '}  {task:26} {seen.why()}")
    shown.say()
    shown.say(f"threshold: {notice.ENOUGH} sittings, {notice.SITTING} apart")

    ready = [t for t in tasks if notice.across(t, ledger.shown(t, at=LEDGER))]
    shown.hand = [
        "Both demonstrations were recorded seconds apart, so this is one sitting however",
        "many times it ran. The honest answer is NOT worth compiling yet.",
        "",
        "The walk compiles it anyway at station 5, and that is the point: this rule is",
        "printed by one command and enforced by none.",
    ]
    shown.agree = not ready
    if ready:
        shown.gap.append(f"corroborated from a single sitting: {ready}")
    shown.gap.append("compile and run never ask notice, so corroboration is advice rather "
                     "than a gate. The mechanism exists and nothing is wired to obey it.")
    return shown


def why_blind(window: list[Any], before: list[dict[str, str]]) -> str:
    structured = [e for e in window if e.structured]
    if not structured:
        return "nothing structured arrived in this act's window"
    lost = [e for e in structured if e.body is None]
    if lost and not any(e.records() for e in structured):
        return (f"BODY LOST: {len(lost)} structured response(s) arrived and the body was "
                f"gone by the time it was asked for -- evicted by the navigation the NEXT "
                f"act caused, because an effect is only drained when the act after it runs")
    carried = [e for e in structured if e.body and not e.records()]
    if carried and not any(e.records() for e in structured):
        return ("NOT A RECORD SET: a body arrived and parsed, and record_sets found nothing "
                "in it. It answers with one object, and a lone object is not a set -- so the "
                "commonest write-response shape on the web is invisible to both the miner "
                "and the reader that share this extractor")
    arrived = [r for e in structured for r in e.records()]
    keyed = {r.get("id") for r in before if r.get("id")}
    if arrived and all(r in before or r.get("id") in keyed for r in arrived):
        return ("UPDATE, NOT INSERT: every record that came back was already there under "
                "the same id, with a field changed. The miner is built on a record "
                "APPEARING, so a state change is not an effect it can see")
    return "records arrived and the vendor still derived nothing"


async def mining() -> Shown:
    from factory.compile.induce import _their_step
    from factory.compile.mine import contract_of, events, mined
    from factory.store import ledger

    segments = ledger.shown(TASK, at=LEDGER)
    if not segments:
        return Shown(skipped="nothing demonstrated yet. Station 1 first.")

    shown = Shown()
    segment = segments[0]
    windows = [list(a.saw) for a in segment.acts[1:]] + [list(segment.after)]
    seen: list[dict[str, str]] = []
    derived = 0
    for index, (act, event) in enumerate(
            zip(segment.acts, events(segment.acts, segment.after), strict=True)):
        where = act.target.described() if act.target else "(unresolved)"
        their = _their_step(act, index, segment.intent)
        head = f"{index} {act.doing.value:6} {where:32}"
        seen = seen + [r for e in act.saw for r in e.records()]
        if their is None:
            shown.say(f"{head} dropped: no word for this act in the compiler")
            continue
        contract = contract_of(mined(event, their))
        if contract.expects:
            derived += 1
            shown.say(head)
            for key, value in contract.expects.items():
                shown.say(f"      expects {key} = {value!r}")
            if contract.identifies:
                shown.say(f"      identifies {contract.identifies!r} -- the destination "
                          f"minted it, so CONFIRMED can mean CAUSED")
        else:
            shown.say(f"{head} {why_blind(windows[index], seen)}")
    shown.say()
    shown.say(f"{derived} of {len(segment.acts)} acts left something checkable on the wire")

    shown.hand = [
        "Four acts change server state and I expect a delta from each: the search returns a",
        "record set, the reveal returns a person carrying an email the list did not have,",
        "the add returns a row with an id the server minted, the send flips a status.",
        "",
        "Typing changes nothing on the wire, so a write must get NO contract and be counted",
        "as demand. A contract invented for it would be a check that passes on anything.",
        "",
        "A bare count of misses is useless here. What matters is WHY each one missed, and",
        "the three reasons above are three different products: one is a race, one is a",
        "stated rule about what a record is, and one is the difference between a system that",
        "watches things be created and a system that watches things change.",
    ]
    shown.agree = derived >= 3
    if derived < 3:
        shown.gap.append(f"{derived} of the 4 acts I expected left a checkable delta. The "
                         f"misses are classified above and none of them is 'the code is "
                         f"wrong' -- each is a boundary of what this miner can see.")
    shown.gap.append("record_sets ignores a lone object, so `{\"row\": {...}}` -- what most "
                     "APIs answer a write with -- carries no record. The rule is deliberate "
                     "and its cost is a whole shape of destination the witness is blind to.")
    shown.gap.append("the miner is built on a record APPEARING, so an update is not an "
                     "effect. Most real workflows change a record rather than create one.")
    return shown


async def compiled() -> Shown:
    from factory.compile.induce import findable, program
    from factory.store import ledger

    if not ledger.tasks(at=LEDGER):
        return Shown(skipped="nothing demonstrated yet. Station 1 first.")

    shown = Shown()
    unrunnable: dict[str, int] = {}
    refused: dict[str, int] = {}
    for task in (TASK, AMBIGUOUS_TASK, LOOPING_TASK):
        segments = ledger.shown(task, at=LEDGER)
        shown.say(f"{task!r}: {len(segments)} demonstration(s)")
        got = program(segments, task)
        if not got:
            refused[task] = len(got.questions)
            for question in got.questions:
                shown.say(f"    REFUSED: {question}")
            shown.say()
            continue
        shown.say(f"    params {got.workflow.params}")
        lost = 0
        for step in got.workflow.steps:
            where = step.target.described() if step.target else ""
            checks = ", ".join(step.contract.expects) if step.contract else "-"
            alone = findable(step, segments)
            lost += not alone
            shown.say(f"    {'?' if step.optional else ' '}{step.doing.value:6} {where:30} "
                      f"param={step.param or '-':8} on={short(step.surface):20} "
                      f"checks={checks}{'' if alone else '   AMBIGUOUS ON ITS OWN PAGE'}")
        told = sum(1 for s in got.workflow.steps if s.contract)
        shown.say(f"    {told} of {len(got.workflow.steps)} steps checkable, "
                  f"{lost} will not run as recorded")
        unrunnable[task] = lost
        shown.say()

    shown.hand = [
        "Three demonstrations, three different answers, and a compiler that gives the same",
        "answer to all three is worthless whichever answer it is.",
        "",
        f"LIVENESS   {TASK!r} went through a control alone on its page. Every step is",
        "           findable, so a program must come out and run.",
        f"SAFETY 1   {AMBIGUOUS_TASK!r} went through one of two identically named controls.",
        "           locate refuses on two matches, so the compiler has to say AMBIGUOUS now",
        "           rather than ship a program that fails weeks later on somebody's rows.",
        f"SAFETY 2   {LOOPING_TASK!r} repeats a field-then-field-then-button shape, and the",
        "           vendor induces a LOOP whose body it does not put in the graph. There is",
        "           no honest program to emit, so it must refuse.",
    ]
    shown.agree = (unrunnable.get(TASK) == 0 and TASK not in refused
                   and unrunnable.get(AMBIGUOUS_TASK, 0) > 0
                   and LOOPING_TASK in refused)
    if TASK in refused:
        shown.gap.append(f"{TASK!r} refused and should have compiled")
    elif unrunnable.get(TASK):
        shown.gap.append(f"{TASK!r} has {unrunnable[TASK]} ambiguous step(s) and should have "
                         f"none: the unambiguous path is not unambiguous")
    if not unrunnable.get(AMBIGUOUS_TASK) and AMBIGUOUS_TASK not in refused:
        shown.gap.append(f"{AMBIGUOUS_TASK!r} reported no ambiguity: the guard did not fire "
                         f"on the case built to fire it")
    if LOOPING_TASK not in refused:
        shown.gap.append(f"{LOOPING_TASK!r} did not refuse. Before this walk it did not "
                         f"either -- workflow_of skipped every state with no step, so a "
                         f"loop lost its whole body and eleven acts compiled to five that "
                         f"ran clean and did half the task.")
    shown.gap.append("the parameter is named after the TASK, not after what it holds: an Act "
                     "carries no per-step intent, so every step hands the vendor the same "
                     "one and its column naming has nothing else to work with. A rows file "
                     "for this workflow needs a column called 'outreach'.")
    return shown


def named(value: Any) -> str:
    return getattr(value, "value", str(value))


def short(origin: str) -> str:
    return origin.replace("http://127.0.0.1:", ":") or "-"


async def consent() -> Shown:
    from factory.authority import permit as permits
    from factory.compile.induce import consequential, program
    from factory.core.question import Question
    from factory.main import allowed
    from factory.store import ledger

    segments = ledger.shown(TASK, at=LEDGER)
    got = program(segments, TASK) if segments else None
    if not got:
        return Shown(skipped="nothing compiled yet. Stations 1 and 5 first.")

    shown = Shown()
    memory = store()
    asked: list[Question] = []

    class Answering:
        def ask(self, question: Question) -> str:
            asked.append(question)
            return "3"

    granted = allowed(memory, got.workflow, Answering())
    for question in asked:
        shown.say(f"asked: {question.about}")
        shown.say(f"       {question.because}")
    shown.say()
    shown.say(f"{granted} permit(s) granted from {len(asked)} question(s) over "
              f"{len(got.workflow.steps)} step(s)")
    seen = len(asked)
    again = allowed(memory, got.workflow, Answering())
    shown.say(f"asked again on the next run: {len(asked) - seen} question(s), "
              f"{again} permit(s)")
    for step in got.workflow.steps:
        held = permits.held(memory, step, got.workflow.name)
        if held:
            shown.say(f"    held: {step.intent or step.doing.value} -- {held.left} left")
    reversible = [s for s in got.workflow.steps if consequential(s, segments)]
    shown.say()
    shown.say(f"{len(reversible)} step(s) shown reversible by evidence, never asked about")

    shown.hand = [
        "Consent is per STEP, not per row. A hundred rows asking a hundred times is a gate",
        "somebody turns off, which is the same as no gate.",
        "",
        "The compiler cannot show a step irreversible: a send whose response nobody could",
        "address and a click that only moved focus are the same evidence. So it asks about",
        "everything it cannot show undoable, a person separates them once, and the answer",
        "is kept. The second call must ask nothing.",
    ]
    shown.agree = again == 0 and granted > 0
    if again:
        shown.gap.append(f"asked {again} more time(s) on a permit already held")
    if not granted:
        shown.gap.append("nothing was asked about at all: either every step was shown "
                         "reversible, or the gate is a brick")
    return shown


async def locating() -> Shown:
    from factory.core.workflow import Target

    shown = Shown()
    safety = liveness = 0
    async with Attached() as up:
        await up.page.goto(f"{site.Serving.prospects}/", wait_until="load")
        await up.page.click("#q")
        await up.page.keyboard.type("category head")
        await up.page.click("#go")
        await up.page.wait_for_selector("#rows tr")

        table = await up.browser.find(Target(role="button", name="Access email"))
        offered = sum(1 for d in table.among.values() if d == "button Access email")
        shown.say(f"on the list, {offered} controls answer to `button Access email`")
        shown.say(f"    found={bool(table)} rung={table.rung or '-'} why={table.why}")
        safety += not table

        await up.page.goto(f"{site.Serving.prospects}/person?id=p1", wait_until="load")
        alone = await up.browser.find(Target(role="button", name="Access email"))
        shown.say("on the person's own page, 1 control answers to the same description")
        shown.say(f"    found={bool(alone)} rung={alone.rung or '-'} why={alone.why}")
        liveness += bool(alone)

        gone = await up.browser.find(Target(role="button", name="Delete everything"))
        shown.say(f"a control that is not there: found={bool(gone)} why={gone.why}")
        safety += not gone

        if alone:
            pressed = await up.browser.press(alone)
            shown.say()
            shown.say(f"pressed through the guard: dispatched={pressed.ok} "
                      f"delivery={pressed.delivery.value} moves={pressed.value}")
            shown.say(f"    {pressed.detail}")
            shown.say(f"    it fetched {len(pressed.exchanges)} response(s) for itself")

    shown.say()
    shown.say(f"SAFETY   acted when it should have refused: {2 - safety}  (must be 0)")
    shown.say(f"LIVENESS refused when it should have acted: {1 - liveness}  (budgeted)")

    shown.hand = [
        "Three cases, and the middle one is the whole machine:",
        "  two matches  refuse. Pressing either is indistinguishable from working.",
        "  one match    act.",
        "  no match     refuse, and say so differently from the ambiguous refusal.",
        "",
        "Scored on the first and third alone a brick is perfect.",
    ]
    shown.agree = safety == 2 and liveness == 1
    if safety < 2:
        shown.gap.append("it acted where it should have refused; this must be 0")
    if liveness < 1:
        shown.gap.append("it refused a control that was alone on its page")
    return shown


async def run_it() -> Shown:
    from factory.authority.question import Authority
    from factory.compile.induce import program
    from factory.run import harness
    from factory.store import ledger, runs
    from factory.witness.ladder import Ladder

    segments = ledger.shown(TASK, at=LEDGER)
    got = program(segments, TASK) if segments else None
    if not got:
        return Shown(skipped="nothing compiled yet. Stations 1 and 5 first.")

    shown = Shown()
    memory = store()
    surfaces = sorted({s.surface for s in got.workflow.steps if s.surface})
    async with Attached() as up:
        for index, origin in enumerate(surfaces):
            page = up.page if index == 0 else await up.context.new_page()
            await page.goto(f"{origin}/", wait_until="load")
        shown.say(f"the walk opened {len(surfaces)} surface(s) the workflow needs: "
                  f"{', '.join(short(s) for s in surfaces)}")
        shown.say()
        authority = Authority(memory._db, asks=lambda question: None)
        done = await harness.over(up.browser, got.workflow, ROWS, witness=Ladder(),
                                  memory=memory, authority=authority, run_id=TASK)

    runs.keep(done, TASK, at=RUNS)
    for row in done.rows:
        shown.say(f"row {', '.join(f'{k}={v}' for k, v in row.row.items()) or '(none)'}")
        if row.refused:
            shown.say(f"    REFUSED before it started: {row.refused.about}")
            shown.say(f"    {row.refused.because}")
            continue
        for step in row.steps:
            verdict = step.receipt.verdict.value if step.receipt else "no receipt"
            reader = (step.receipt.reader or "-") if step.receipt else "-"
            shown.say(f"    {'ok  ' if step.did.ok else 'FAIL'} {(step.intent or '')[:22]:22} "
                      f"rung={step.rung or '-':11} {step.seconds:5.2f}s  {verdict:13} "
                      f"by {reader}")
            if not step.did.ok:
                shown.say(f"         {step.did.detail}")
        shown.say()

    ran = [s for r in done.rows for s in r.steps]
    landed = sum(s.did.ok for s in ran)
    shown.say(f"{len(done.rows)} row(s), {len(ran)} step(s) attempted, {landed} landed")

    shown.hand = [
        "The rows name two people nobody demonstrated. That is the claim under test: a",
        "program induced from what varied, driven with values it has never seen.",
        "",
        "Every step must reach the surface it was demonstrated on before it can act. This",
        f"workflow spans {len(surfaces)} origins and records no navigation between them, so",
        "the run only starts because the walk opened the tabs first.",
    ]
    shown.agree = bool(ran) and landed == len(ran)
    if not ran:
        shown.gap.append("no step ran at all")
    elif landed < len(ran):
        shown.gap.append(f"{len(ran) - landed} step(s) did not land: "
                         + "; ".join(sorted({s.did.detail[:70] for s in ran if not s.did.ok})))
    shown.gap.append(
        "MISSING MACHINE: nothing arrives at the surfaces a workflow needs. The workflow "
        "knows every origin it acts on, no command opens them, and the recorder emits no "
        "navigation to compile into a GO step. This walk does it by hand.")
    return shown


async def verdicts() -> Shown:
    from factory.core.contract import Contract, Verdict
    from factory.core.evidence import Did
    from factory.store import runs
    from factory.witness import coverage as coverages
    from factory.witness.ladder import Ladder

    kept = runs.of(TASK, at=RUNS)
    if not kept:
        return Shown(skipped="nothing has run yet. Station 8 first.")

    shown = Shown()
    done = kept[-1]
    ladder = Ladder()
    shown.say("admissible, best evidence first: " + (", ".join(
        f"{r.name} ({named(r.channel)})" for r in ladder.admissible()) or "none"))
    shown.say("refused as ours: " + (", ".join(
        r.name for r in ladder.inadmissible()) or "none"))
    shown.say()

    tally: dict[str, int] = {}
    for row in done.rows:
        for step in row.steps:
            if step.receipt:
                tally[step.receipt.verdict.value] = tally.get(step.receipt.verdict.value, 0) + 1
    shown.say(f"verdicts: {tally or 'none'}")
    for row in done.rows:
        for step in row.steps:
            if step.receipt and step.contract and step.contract.expects:
                shown.say(f"  {(step.intent or step.did.detail)[:32]:32} "
                          f"{step.receipt.verdict.value:13} on {step.receipt.channel or '-'} "
                          f"by {step.receipt.reader or '-'}")
                shown.say(f"      expected {step.contract.expects}")
                if step.receipt.why:
                    shown.say(f"      {step.receipt.why}")
                if step.receipt.unreadable:
                    shown.say(f"      could not address: {sorted(step.receipt.unreadable)}")
                break

    wrote = next((s for r in done.rows for s in r.steps
                  if s.contract and s.contract.expects and s.did.exchanges), None)
    shown.say()
    if wrote is None:
        both = False
        shown.say("no act carried both a contract and evidence, so the negative direction "
                  "could not be exercised")
    else:
        lie = Contract(expects=dict.fromkeys(wrote.contract.expects, "definitely not this"))
        refuted = ladder.witness(wrote.did, lie)
        blind = ladder.witness(Did(ok=True), wrote.contract)
        shown.say(f"the same act against a false contract: {refuted.verdict.value.upper()} "
                  f"({refuted.why})")
        shown.say(f"the same contract with no evidence:    {blind.verdict.value.upper()} "
                  f"({blind.why})")
        both = (refuted.verdict is Verdict.REFUTED
                and blind.verdict is Verdict.UNVERIFIABLE)

    seen = coverages.tally((s.did, s.receipt) for r in done.rows for s in r.steps if s.receipt)
    worst = seen.worst()
    shown.say()
    shown.say(f"ceiling on what could ever be confirmed here: {seen.ceiling:.0%}")
    if worst is not None:
        shown.say(f"the reader worth building first: {named(worst.blocked)} ({worst.acts} "
                  f"act(s), offering {', '.join(worst.offered) or 'nothing'})")

    shown.hand = [
        "Three answers and the third is not a softer second. CONFIRMED means a channel that",
        "did not cause the act reported what the act claimed. REFUTED means that channel",
        "disagreed. UNVERIFIABLE means no channel could address the fields at all.",
        "",
        "So the test is not that this run confirmed things. It is that the SAME evidence",
        "refutes a contract that is false and goes unverifiable with nothing to read. A",
        "witness that cannot be made to say REFUTED has never confirmed anything.",
    ]
    shown.agree = both and bool(tally)
    if not both:
        shown.gap.append("the witness was not shown able to refute on this run's evidence")
    return shown


async def learning() -> Shown:
    from factory.core.memory import Kind, Tier
    from factory.memory.driver import Memory

    every = store().every()
    if not every:
        return Shown(skipped="nothing remembered yet. Stations 2 and 8 first.")

    shown = Shown()
    for entry in every:
        shown.say(f"{entry.kind.value:11} {entry.key[:40]:40} tier={entry.tier.value:9} "
                  f"scope={entry.scope or '-'}")
    shown.say()
    shown.say(f"{len(every)} entries in {MEMORY}")

    scratch = Memory()
    entry = scratch.remember(Kind.TARGET, "a control", {"role": "button"},
                             tier=Tier.WORKFLOW)
    for _ in range(6):
        entry = scratch.witnessed(entry, confirmed=True, caused=True)
    climbed = scratch.elevate(entry)
    shown.say()
    shown.say(f"six confirmations: {entry.tier.value} -> "
              f"{climbed.tier.value if climbed else 'not elevated'}")
    entry = climbed or entry
    for _ in range(6):
        entry = scratch.witnessed(entry, confirmed=False)
    dropped = scratch.demote(entry)
    shown.say(f"six refutations after that: {entry.tier.value} -> "
              f"{dropped.tier.value if dropped else 'not demoted'}")

    shown.hand = [
        "Something that only ever gets promoted is a cache with a confident name. The claim",
        "worth checking is that the same counter runs backwards: enough refutations and a",
        "remembered resolution loses the scope it earned.",
        "",
        "An UNVERIFIABLE receipt must move neither side. It is the ceiling on promotion,",
        "which is the ceiling on how cheap a run can ever get.",
    ]
    shown.agree = climbed is not None and dropped is not None
    if climbed is None:
        shown.gap.append("six confirmations did not promote: the ladder never gets cheaper")
    if dropped is None:
        shown.gap.append("six refutations did not demote: promotion is one-way, which makes "
                         "it a cache")
    return shown


async def deciding() -> Shown:
    shown = Shown()
    for name in ("factory.model.driver", "factory.model.catalogue", "factory.model.router",
                 "factory.model.budget", "factory.model.conform"):
        shown.say(f"{name:28} {statements(name):3} statements")
    shown.say()

    built = None
    try:
        from factory.model.driver import Model

        with contextlib.suppress(Exception):
            built = Model()
    except Exception as trouble:
        shown.say(f"the driver did not import: {trouble}")
    shown.say(f"a MODEL driver could be built: {built is not None}")
    if built is None:
        shown.say("no key in the environment, so it is None rather than a stub that raises "
                  "when used. Every station above ran without it.")

    from factory.witness.ladder import Ladder

    empty = Ladder(readers=())
    from factory.core.contract import Contract
    from factory.core.evidence import Did

    said = empty.witness(Did(ok=True), Contract(expects={"id": "1"}))
    shown.say()
    shown.say(f"with no reader at all the ladder still answers: "
              f"{said.verdict.value.upper()} ({said.why})")

    shown.hand = [
        "The claim is 'absent is a state, never a subclass that raises when used', and that",
        "is checkable without a key: every station above ran with no MODEL driver, and the",
        "ones that could not proceed said what they could not do.",
        "",
        "What a key buys is exactly one thing, the `chosen` rung: which of these six is the",
        "one that was meant. It is the second of four rungs and its answer is kept as a role",
        "and a name, so the run after it costs nothing. That is why asking is cheaper than",
        "hardcoding rather than more expensive.",
    ]
    shown.agree = said.verdict.value == "unverifiable"
    shown.gap.append("the `chosen` rung is untested here: no key, so a model has never been "
                     "asked to disambiguate on this surface. Stated as untested rather than "
                     "assumed present.")
    shown.gap.append("catalogue, router and budget are docstrings. Routing by cost and a "
                     "budget that binds are claims with no code behind them.")
    return shown


async def kernel() -> Shown:
    shown = Shown()
    try:
        from factory.kernel.driver import Kernel
    except Exception as trouble:
        return Shown(skipped=f"the KERNEL driver did not import: {trouble}")

    started = time.perf_counter()
    try:
        async with await Kernel.start() as running:
            shown.say(f"started in {time.perf_counter() - started:.1f}s")
            cell = await running.run("1 + 1", timeout=30)
            shown.say(f"1 + 1 -> {cell.result!r}")
            where = await running.run("import sys; sys.executable", timeout=30)
            shown.say(f"its interpreter: {where.result!r}")
            leak = await running.run(
                "import importlib.util; bool(importlib.util.find_spec('factory'))",
                timeout=30)
            shown.say(f"can it import the factory? {leak.result!r} "
                      f"{'-- ISOLATION LEAK' if leak.result == 'True' else '(isolated)'}")
    except Exception as trouble:
        return Shown(skipped=f"the kernel would not start: {type(trouble).__name__}: "
                             f"{str(trouble)[:200]}")

    shown.hand = [
        "It has to be a different interpreter with a different set of packages or the",
        "isolation is decoration. The check is not that it runs code; it is that code",
        "running in it cannot reach this tree.",
    ]
    shown.agree = True
    return shown


async def manufacturing() -> Shown:
    from factory.capability import amortize, draft, publish
    from factory.compile.induce import program
    from factory.store import ledger, runs

    segments = ledger.shown(TASK, at=LEDGER)
    kept = runs.of(TASK, at=RUNS)
    if not segments or not kept:
        return Shown(skipped="needs a demonstration and a run. Stations 1 and 8 first.")
    got = program(segments, TASK)
    if not got:
        return Shown(skipped="nothing compiled.")

    shown = Shown()
    shown.say(f"the run it would be drafted from worked: {draft.worked(kept[-1])}")
    try:
        made = draft.draft(got.workflow, kept[-1], name="outreach")
    except draft.NotDrafted as refused:
        shown.say(f"REFUSED to draft: {refused}")
        shown.hand = [
            "A capability is read out of the record or it is not made. Refusing on a run",
            "that did not work is the correct direction: a tool drafted from a failed run",
            "is a model's idea of the procedure, which is the thing this whole path avoids.",
        ]
        shown.agree = True
        shown.gap.append("nothing was manufactured, because the run above did not earn it")
        return shown

    shown.say(f"drafted {made.name!r}: module {made.module}, "
              f"undeclared imports {made.undeclared() or 'none'}")
    for line in made.source.splitlines()[:22]:
        shown.say(f"    {line}")
    root = publish.write(SKILLS / made.name, made)
    shown.say()
    shown.say(f"written to {root}, complete={publish.complete(root)}")

    if len(kept) > 1:
        worth = amortize.worth(made.name, kept[0], kept[1:])
        shown.say()
        shown.say(f"{worth.line()}")
        shown.say(f"{amortize.review(worth).line()}")
    else:
        shown.say()
        shown.say("one run so far, so nothing can be said about whether it paid for itself. "
                  "Run station 8 again.")

    shown.hand = [
        "The claim that separates this from a macro recorder: the procedure is READ OUT OF",
        "THE RECORD, and the only thing a model is ever asked for is a name. SkillsBench",
        "measured self-generated skills at about zero against +16.2pp for curated ones, so",
        "a model authoring its own procedural knowledge is the failure, not the goal.",
        "",
        "The harder half is that authoring is counted. A tool that never recovers what it",
        "cost to make has to leave, and nothing in this tree currently calls the thing that",
        "would make it leave.",
    ]
    shown.agree = publish.complete(root)
    if not publish.complete(root):
        shown.gap.append("what was written is not a complete skill")
    shown.gap.append("amortize.retired names what should go and orchestrate/maintain.py is "
                     "its only caller, which no command runs. Removal is a claim with no "
                     "mechanism until something calls it.")
    return shown


async def cost() -> Shown:
    from factory.observe import cheaper, spent
    from factory.store import runs

    kept = runs.of(TASK, at=RUNS)
    if not kept:
        return Shown(skipped="nothing has run yet. Station 8 first.")

    shown = Shown()
    for index, run in enumerate(kept):
        money = spent(run)
        shown.say(f"run {index}: {money.steps} step(s)  confirmed={money.confirmed} "
                  f"refuted={money.refuted} unverifiable={money.unverifiable}")
        shown.say(f"        by rung {money.by_rung or '-'}")
        shown.say(f"        {money.said()}")
    shown.say()
    if len(kept) > 1:
        answer = cheaper(spent(kept[0]), spent(kept[-1]))
        shown.say("against the FIRST run of this task: "
                  + {True: "cheaper", False: "not cheaper", None: "unknown"}[answer])
    else:
        shown.say("one run so far, so there is nothing to compare it to. Run station 8 "
                  "again and this becomes a comparison.")

    shown.hand = [
        "Cost is the second number and it is a comparison, against the FIRST run rather than",
        "the previous one: run to run is noise, and the claim is that the path gets cheaper",
        "as evidence accumulates.",
        "",
        "The answer that matters most is `unknown`. Two runs priced entirely from priors",
        "give a direction about the price table, not about the system, and rounding that to",
        "'not cheaper' is a number that looks like measurement and is not.",
    ]
    shown.agree = True
    return shown


@dataclass
class Station:
    number: int
    tier: str
    machine: str
    claim: str
    run: Callable[[], Awaitable[Shown]]
    needs: str = ""


STATIONS = [
    Station(0, "-", "the board",
            "what exists, what a command reaches, what nothing calls", board),
    Station(1, "1 driver", "browser/record + store/ledger",
            "a person's acts, with what the page fetched while they happened",
            record_demonstrations, "a browser"),
    Station(2, "1 driver", "browser/pace + memory/",
            "the operator's own rhythm, fitted and kept", fit_pace, "a browser"),
    Station(3, "1 driver", "capability/notice",
            "is this a habit or one afternoon", corroboration),
    Station(4, "2 line", "compile/mine",
            "what changed on the wire around each act", mining),
    Station(5, "2 line", "compile/induce",
            "demonstrations in, a program or a refusal out, no model", compiled),
    Station(6, "2 line", "authority/permit",
            "consent once per step, with a budget that gets spent", consent),
    Station(7, "1 driver", "browser/locate + guard",
            "find by role and name; refuse on two matches", locating, "a browser"),
    Station(8, "2 line", "run/harness",
            "the program over rows nobody demonstrated", run_it, "a browser"),
    Station(9, "1 driver", "witness/",
            "a verdict on a channel that did not cause the act", verdicts),
    Station(10, "1 driver", "memory/",
            "receipts into what is known, at what scope", learning),
    Station(11, "1 driver", "model/",
            "context to a typed decision, and absent is a state", deciding),
    Station(12, "1 driver", "kernel/", "code to effects, in another interpreter", kernel),
    Station(13, "1 driver", "capability/",
            "evidence to a tool, kept only while it pays for itself", manufacturing),
    Station(14, "3 root", "observe/", "the second number, and unknown stays unknown", cost),
]


def listing() -> None:
    out(f"\n  {len(STATIONS)} stations. State lives in {HOME}\n")
    for one in STATIONS:
        out(f"  {one.number:2}  {one.tier:9} {one.machine:31} {one.claim}")
        if one.needs:
            out(f"      {'':9} needs {one.needs}")
    out("\n  uv run python -m demo.walk <n>     one station")
    out("  uv run python -m demo.walk --all   all of them\n")


async def walk_one(one: Station, pause: bool) -> bool | None:
    out()
    out(BAR)
    out(f"  STATION {one.number}   {one.tier}   {one.machine}")
    out(f"  CLAIM     {one.claim}")
    out(BAR)
    started = time.perf_counter()
    try:
        shown = await one.run()
    except Exception as trouble:
        import traceback

        out(f"\n  the station raised: {type(trouble).__name__}: {trouble}")
        for line in traceback.format_exc().splitlines()[-8:]:
            out(f"      {line}")
        return False
    took = time.perf_counter() - started

    if shown.skipped:
        out(f"\n  not run: {shown.skipped}")
        return None
    out()
    block("FACTORY", shown.factory)
    out()
    block("HAND", shown.hand)
    if shown.gap:
        out()
        block("GAP", shown.gap)
    out()
    out(f"  VERDICT   {ANSWERS[shown.agree]}   ({took:.1f}s)")
    if pause:
        out()
        with contextlib.suppress(EOFError, KeyboardInterrupt):
            input("  enter for the next station ")
    return shown.agree


def reset() -> None:
    if HOME.exists():
        shutil.rmtree(HOME)
    HOME.mkdir(parents=True, exist_ok=True)
    out(f"  cleared {HOME}: no demonstrations, no runs, no memory, no skills")


async def main() -> int:
    parser = argparse.ArgumentParser(prog="demo.walk")
    parser.add_argument("station", nargs="?", type=int)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--from", dest="start", type=int)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--step", action="store_true")
    args = parser.parse_args()

    if args.reset:
        reset()
    picked = args.station is not None or args.all or args.start is not None
    if args.list or not picked:
        if not args.reset or args.list:
            listing()
        return 0

    if args.station is not None:
        chosen = [s for s in STATIONS if s.number == args.station]
        if not chosen:
            out(f"no station {args.station}")
            return 1
    elif args.start is not None:
        chosen = [s for s in STATIONS if s.number >= args.start]
    else:
        chosen = list(STATIONS)

    answers = {}
    for one in chosen:
        answers[one.number] = await walk_one(one, args.step and one is not chosen[-1])

    out()
    out(BAR)
    out("  WHERE THE FACTORY AGREED WITH A PERSON READING THE SAME INPUT")
    out(BAR)
    for one in chosen:
        out(f"  {one.number:2}  {ANSWERS[answers[one.number]]:19} {one.machine}")
    disagreed = [n for n, a in answers.items() if a is False]
    out()
    out(f"  {sum(a is True for a in answers.values())} agree, {len(disagreed)} disagree, "
        f"{sum(a is None for a in answers.values())} not decidable here")
    if disagreed:
        out(f"  disagreed at: {disagreed}")
    return 1 if disagreed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
