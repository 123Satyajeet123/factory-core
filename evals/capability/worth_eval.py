"""Is this worth a name, or does the library already have one for it?

    uv run python -m evals.capability.worth_eval

No browser and no site. Workflows only, because what is under test is whether a procedure
encodes anything and whether anything else already encodes it.

    ADMITTED  a stock interaction or a duplicate got a name   must be 0
    REFUSED   a real procedure was called stock               must be 0
"""

from __future__ import annotations

import sys

from factory.capability.worth import SAME, closest, judge, shape, stock
from factory.core.verbs import Doing
from factory.core.workflow import Step, Target, Workflow


def flow(name: str, *steps: Step, params: tuple[str, ...] = ("note",)) -> Workflow:
    return Workflow(name=name, steps=list(steps), params=params)


GO = Step(doing=Doing.GO, value="http://example.invalid/form", surface="one")
NOTE = Step(doing=Doing.WRITE, param="note", surface="one",
            target=Target(role="textbox", name="Note"))
BODY = Step(doing=Doing.WRITE, param="note", surface="one",
            target=Target(role="textbox", name="Body"))
SAVE = Step(doing=Doing.PRESS, surface="one", target=Target(role="button", name="Save"))
SEND = Step(doing=Doing.PRESS, surface="two", target=Target(role="button", name="Send"))

REAL = flow("file-a-note", GO, NOTE, SAVE, SEND)


def run() -> int:
    admitted = refused = failed = 0

    def check(name: str, ok: bool, detail: str) -> None:
        nonlocal failed
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name:50} {detail}")

    # W1 -- a real procedure is worth a name.
    good = judge(REAL, {})
    refused += not good
    check("W1 a four-step procedure is worth a name", bool(good), good.why())

    # W2 -- one act is an act.
    one = judge(flow("press-save", SAVE), {})
    admitted += bool(one)
    check("W2 one step is not a procedure", not one, one.why())

    # W3 -- no parameters means it does the same thing forever.
    fixed = judge(flow("always-the-same", GO, SAVE, SEND, params=()), {})
    admitted += bool(fixed)
    check("W3 no parameters is a bookmark, not a tool", not fixed, fixed.why())

    # W4 -- two steps on one surface is what any page offers.
    plain = judge(flow("type-and-press", NOTE, SAVE), {})
    admitted += bool(plain)
    check("W4 two steps on one surface is stock", not plain, plain.why())

    # W5 -- VALUES ARE NOT PART OF THE SHAPE. The same procedure with different arguments
    # is one capability, or a library fills with one entry per row of a spreadsheet.
    check("W5 the shape ignores what was written",
          shape(REAL) == shape(flow("same-again", GO, NOTE, SAVE, SEND)),
          " -> ".join(shape(REAL)))

    # W6 -- and something already installed does not get a second name.
    library = {"file-a-note": shape(REAL)}
    twin = judge(flow("note-filer", GO, NOTE, SAVE, SEND), library)
    admitted += bool(twin)
    check("W6 an exact duplicate is refused", not twin, twin.why())

    # W7 -- a near-duplicate: the same targets with one step dropped. MEASURED at 0.857.
    varied = flow("nearly", GO, NOTE, SAVE)
    near = judge(varied, library)
    _, alike = closest(shape(varied), library)
    admitted += bool(near)
    check("W7 the same procedure, one step short, is refused", not near, near.why())

    # W7b -- but a different FIELD is a different procedure, not a variation of this one.
    # Measured at 0.750, and the threshold sits above it on purpose.
    renamed = flow("writes-elsewhere", GO, BODY, SAVE, SEND)
    _, other_alike = closest(shape(renamed), library)
    refused += not judge(renamed, library)
    check("W7 a different target is a different procedure",
          bool(judge(renamed, library)), f"{other_alike:.0%} alike, and admitted")

    # W8 -- but something genuinely different is not.
    other = flow("different", GO, NOTE, Step(doing=Doing.KEY, value="Enter", surface="one"))
    apart = judge(other, library)
    refused += not apart
    check("W8 a different procedure is admitted", bool(apart), apart.why())

    # W9 -- what the knob admits, printed rather than asserted.
    print(f"\n  a step dropped scores {alike:.3f}; a field renamed scores {other_alike:.3f}")
    print("  threshold   one step dropped   a field renamed   a different tail")
    for edge in (0.70, 0.85, 0.95, 1.00):
        a = bool(judge(varied, library, same=edge))
        b = bool(judge(renamed, library, same=edge))
        c = bool(judge(other, library, same=edge))
        row = [("admitted" if x else "refused") for x in (a, b, c)]
        print(f"  {edge:>9.2f}   {row[0]:18}{row[1]:18}{row[2]}")
    check("W9 the shipped threshold sits in the measured gap",
          not bool(judge(varied, library, same=SAME))
          and bool(judge(renamed, library, same=SAME))
          and bool(judge(other, library, same=SAME)), f"SAME = {SAME}")

    # W10 -- stock is checked before duplication, because a stock interaction is not worth
    # a name whatever else is installed.
    lone = flow("press-save", SAVE)
    check("W10 stock is answered without the library",
          bool(stock(lone)) and not judge(lone, library).duplicate,
          "one step, and no comparison needed")

    print(f"\nADMITTED a stock interaction or a duplicate : {admitted}   (must be 0)")
    print(f"REFUSED  a real procedure called stock      : {refused}   (must be 0)")
    print(f"FAILED   cases not matching                 : {failed}")
    return 1 if admitted or refused or failed else 0


if __name__ == "__main__":
    sys.exit(run())
