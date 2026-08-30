"""A real demonstration contains things that are not the task.

    uv run python -m evals.compile.noise_eval

Somebody who says "watch this" still answers a message, clicks a heading, mistypes and
corrects. If two traces only align when they are identical, no recording a person makes
will ever induce -- and every property below decides whether this works on the first real
one or only on ours.
"""

from __future__ import annotations

import json
import sys

from factory.compile.induce import program
from factory.core.evidence import Exchange
from factory.core.ledger import Act, Segment, Whose
from factory.core.verbs import Doing
from factory.core.workflow import Target

NAME = Target(role="textbox", name="Name")
SAVE = Target(role="button", name="Save")
ASIDE = Target(role="link", name="Inbox")
HEADING = Target(role="heading", name="add a person")


SURFACE = "http://127.0.0.1:8099"


def act(doing: Doing, target: Target, value: str = "") -> Act:
    return Act(doing=doing, target=target, value=value, where=(10, 10),
               box=(0, 0, 20, 20), surface=SURFACE)


def task(who: str) -> list[Act]:
    return [act(Doing.PRESS, NAME), act(Doing.WRITE, NAME, who), act(Doing.PRESS, SAVE)]


#: name, two demonstrations, what must come out
CASES = (
    ("identical", task("Ada Lovelace"), task("Grace Hopper"), "program"),
    ("one answered a message", task("Ada Lovelace"),
     [act(Doing.PRESS, ASIDE), *task("Grace Hopper")], "program"),
    ("both wandered, differently", [act(Doing.PRESS, HEADING), *task("Ada Lovelace")],
     [*task("Grace Hopper"), act(Doing.PRESS, ASIDE)], "program"),
    ("one corrected a typo", task("Ada Lovelace"),
     [act(Doing.PRESS, NAME), act(Doing.WRITE, NAME, "Grace Hoppr"),
      act(Doing.WRITE, NAME, "Grace Hopper"), act(Doing.PRESS, SAVE)], "question"),
)


def answered(*records: dict[str, str]) -> list[Exchange]:
    """What a destination sent back, as the page fetched it."""
    return [Exchange(url=f"{SURFACE}/rows", status=200, content_type="application/json",
                     body=json.dumps(list(records)))]


def contracts() -> int:
    """Does a demonstration that recorded traffic compile to a program that can be CHECKED?

    THE WHOLE POINT, AND IT WAS UNREACHED FOR AS LONG AS `contract_of` HAD NO CALLER. A
    workflow whose steps carry no contract reaches the harness and every verdict is
    UNVERIFIABLE, so the witness -- the one driver with no vendor and the reason this
    project exists -- never ran on real work while its own suite was green.

    THE EVIDENCE IS ON `Segment.after`, WHICH IS THE HARD CASE. The save is the last act;
    its effect arrives after it and there is no next act to carry it.
    """
    faults = 0
    shown = [
        Segment(whose=Whose.PERSON, intent="add a person", acts=task(who),
                after=answered({"id": "1", "name": who}))
        for who in ("Ada Lovelace", "Grace Hopper")
    ]
    got = program(shown, "add a person")
    if not got.workflow:
        print(f"contracts                  FAULT refused: {got.questions[:1]}")
        return 1

    told = [step for step in got.workflow.steps if step.contract]
    for step in got.workflow.steps:
        mark = step.contract.expects if step.contract else "-"
        varies = step.contract.varies if step.contract else {}
        print(f"contracts  {step.doing.value:6} {(step.target.name or ''):8} "
              f"expects={mark}  varies={varies or '-'}  "
              f"needs a permit={step.irreversible}")

    #: BOTH DIRECTIONS ON THE PERMIT GATE. A step the demonstration watched write a record
    #: it can read again does not stop to ask; every step whose consequence nobody observed
    #: does. A predicate that answers one way for everything passes half of this.
    saves = [step for step in got.workflow.steps if step.contract]
    unseen = [step for step in got.workflow.steps if not step.contract]
    if any(step.irreversible for step in saves):
        faults += 1
        print("           FAULT an effect observed landing somewhere readable still asks")
    if unseen and not all(step.irreversible for step in unseen):
        faults += 1
        print("           FAULT a step whose consequence nobody observed does NOT ask, so "
              "an unattended run would send with no permit")

    if not told:
        faults += 1
        print("           FAULT a demonstration WITH traffic produced no contract at all")
    elif not any(step.contract.varies for step in told):
        faults += 1
        print("           FAULT a contract bound the demonstrated value and not the "
              "parameter, so every row would confirm against one demonstration's record")

    #: The other direction. Without evidence there is nothing to bind, and saying so is
    #: correct -- a contract invented here would confirm whatever it was asked.
    blind = [Segment(whose=Whose.PERSON, intent="add a person", acts=task(who))
             for who in ("Ada Lovelace", "Grace Hopper")]
    without = program(blind, "add a person")
    if without.workflow and not all(s.irreversible for s in without.workflow.steps):
        faults += 1
        print("           FAULT a demonstration that observed nothing trusted everything")
    if without.workflow and any(step.contract for step in without.workflow.steps):
        faults += 1
        print("           FAULT a demonstration that recorded nothing invented a contract")
    steps = without.workflow.steps if without.workflow else []
    invented = sum(1 for step in steps if step.contract)
    print(f"contracts  no traffic       -> {invented} contracts (must be 0)")
    return faults


def findability() -> int:
    """Does the compiler say, BEFORE a run, that a step named a control it cannot pick out?

    THE ORDINARY CASE IS A TABLE, and it is where a real workflow dies. Every row carries a
    control with the same role and the same name; a person presses one by where it sits and
    `locate` refuses on two matches. Recorded without `Act.among` this compiles clean and
    refuses weeks later against somebody else's rows.
    """
    from factory.compile.induce import findable

    faults = 0
    alone = ("textbox 'Name'", "button 'Save'", "heading 'add a person'")
    crowd = (*alone, "button 'Save'")

    for label, offering, wanted in (("one of its kind", alone, True),
                                    ("one of six in a table", crowd, False)):
        shown = [
            Segment(whose=Whose.PERSON, intent="add a person",
                    acts=[act.model_copy(update={"among": offering}) for act in task(who)],
                    after=answered({"id": "1", "name": who}))
            for who in ("Ada Lovelace", "Grace Hopper")
        ]
        got = program(shown, "add a person")
        if not got.workflow:
            print(f"findable   {label:22} FAULT refused")
            faults += 1
            continue
        save = next(s for s in got.workflow.steps if (s.target.name or "") == "Save")
        got_it = findable(save, shown)
        print(f"findable   {label:22} press Save -> findable={got_it} (wanted {wanted})")
        if got_it is not wanted:
            faults += 1
            print(f"{'':11} FAULT a control sharing its name with a sibling "
                  f"{'was called findable' if got_it else 'was called ambiguous'}")
    return faults


def main() -> int:
    faults = 0
    for label, first, second, wanted in CASES:
        shown = [Segment(whose=Whose.PERSON, intent="add a person", acts=acts)
                 for acts in (first, second)]
        got = program(shown, "add a person")

        if got.workflow:
            marks = " ".join(
                f"{'?' if s.optional else ' '}{s.doing.value[:2]}:{(s.target.name or '')[:5]}"
                for s in got.workflow.steps)
            needed = [s for s in got.workflow.steps if not s.optional]
            print(f"{label:26} program   {len(needed)} needed of "
                  f"{len(got.workflow.steps)}  [{marks}]")
        else:
            print(f"{label:26} refused   {got.questions[0][:56]}")

        if wanted == "program" and not got.workflow:
            faults += 1
            print(f"{'':26} FAULT a demonstration with an aside must still induce")
        if wanted == "question" and got.workflow:
            faults += 1
            print(f"{'':26} FAULT a divergence it cannot explain must be asked, not guessed")

        #: The task itself is never optional, and what only happened once always is.
        if got.workflow:
            for step in got.workflow.steps:
                incidental = (step.target or NAME).name in {"Inbox", "add a person"}
                if incidental != step.optional:
                    faults += 1
                    print(f"{'':26} FAULT {step.target.described()} optional="
                          f"{step.optional}, wanted {incidental}")

    print()
    faults += contracts()
    print()
    faults += findability()
    print(f"\nFAULTS  {faults}   (must be 0)")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(main())
