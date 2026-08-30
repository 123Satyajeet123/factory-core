"""Does a capability that stopped paying stop being offered?

    uv run python -m evals.capability.amortize_eval

No browser and no site. Synthetic runs carrying rungs, because the whole question is
arithmetic over what `run/select.py` recorded.

    KEPT     a capability that costs more than it saves was kept   must be 0
    DUMPED   one that pays, or one nobody tried, was retired       must be 0
"""

from __future__ import annotations

import sys

from factory.capability.amortize import (
    Standing,
    Worth,
    needed_thinking,
    retired,
    review,
    reviewed,
    worth,
)
from factory.core.evidence import Did, RowRun, Run, StepRun


def a_run(*rungs: str) -> Run:
    return Run(workflow="w", rows=[RowRun(row={}, steps=[
        StepRun(intent=f"s{i}", did=Did(ok=True), rung=r) for i, r in enumerate(rungs)])])


#: Direct execution: four steps, two of which needed somebody to think.
BEFORE = a_run("chosen", "chosen", "structural", "none")


def run() -> int:
    kept = dumped = failed = 0

    def check(name: str, ok: bool, detail: str) -> None:
        nonlocal failed
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name:52} {detail}")

    # M1 -- the unit is observed, and an unrecorded rung is not credited as free.
    check("M1 thinking is counted from the rung", needed_thinking(BEFORE) == 2,
          f"{needed_thinking(BEFORE)} of 4 steps needed a model")
    #: `observe.PRICED` charges an unrecorded rung AS A MODEL, not as free and not as
    #: nothing. That is the safe direction for this arithmetic: it under-credits a
    #: capability rather than crediting it for savings nobody observed.
    check("M1 an unrecorded rung is charged, not forgiven",
          needed_thinking(a_run("", "")) == 2 and needed_thinking(a_run("chosen", "")) == 2,
          "two unrecorded rungs cost two model steps")

    # M2 -- a capability that removes the thinking pays, and says when.
    good = worth("pays", BEFORE, [a_run("remembered", "remembered", "structural", "none")] * 4)
    check("M2 one that removes the thinking pays", good.recovered and good.breakeven == 1,
          good.line())

    # M3 -- THE MEASURED WARNING. One that saves nothing never amortizes, however often used.
    flat = worth("saves-nothing", BEFORE, [BEFORE] * 50)
    check("M3 fifty uses do not rescue a saving of zero",
          not flat.recovered and flat.breakeven is None, flat.line())

    # M4 -- and one that costs MORE is worse than nothing, which is the finding itself.
    worse = worth("costs-more", BEFORE, [a_run("chosen", "chosen", "chosen", "chosen")] * 5)
    check("M4 a capability can be worse than direct execution",
          worse.saved < 0 and worse.breakeven is None, worse.line())

    # M5 -- the sweep decides, and retiring is what stops it being offered.
    seen = reviewed([good, flat, worse])
    names = retired(seen)
    kept += "saves-nothing" not in names or "costs-more" not in names
    dumped += "pays" in names
    check("M5 the sweep retires what stopped paying", set(names) == {"saves-nothing", "costs-more"},
          f"retired {sorted(names)}")

    # M6 -- nothing is retired on silence. Unused is not unworthy.
    untried = review(Worth(name="new", authored=1, saved=0.0, uses=0))
    dumped += untried.standing is Standing.RETIRED
    check("M6 a capability nobody used is held, not judged",
          untried.standing is Standing.UNTRIED, untried.line())

    # M7 -- and one used twice is still too early to judge.
    early = review(worth("early", BEFORE, [BEFORE] * 2))
    dumped += early.standing is Standing.RETIRED
    check("M7 two uses is not enough to retire on", early.standing is Standing.UNTRIED,
          early.line())

    for one in seen:
        print(f"    {one.line()}")

    print(f"\nKEPT   a capability costing more than it saves : {kept}   (must be 0)")
    print(f"DUMPED one that pays, or one nobody tried      : {dumped}   (must be 0)")
    print(f"FAILED cases not matching                      : {failed}")
    return 1 if kept or dumped or failed else 0


if __name__ == "__main__":
    sys.exit(run())
