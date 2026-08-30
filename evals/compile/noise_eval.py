"""A real demonstration contains things that are not the task.

    uv run python -m evals.compile.noise_eval

Somebody who says "watch this" still answers a message, clicks a heading, mistypes and
corrects. If two traces only align when they are identical, no recording a person makes
will ever induce -- and every property below decides whether this works on the first real
one or only on ours.
"""

from __future__ import annotations

import sys

from factory.compile.induce import program
from factory.core.ledger import Act, Segment, Whose
from factory.core.verbs import Doing
from factory.core.workflow import Target

NAME = Target(role="textbox", name="Name")
SAVE = Target(role="button", name="Save")
ASIDE = Target(role="link", name="Inbox")
HEADING = Target(role="heading", name="add a person")


def act(doing: Doing, target: Target, value: str = "") -> Act:
    return Act(doing=doing, target=target, value=value, where=(10, 10), box=(0, 0, 20, 20))


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

    print(f"\nFAULTS  {faults}   (must be 0)")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(main())
