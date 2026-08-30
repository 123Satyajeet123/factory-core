"""Do the failures produce guards, and do the successes produce none?

    uv run python -m evals.capability.variations_eval

No browser and no site. Attempts are built from what a capability returns, so the sweep is
exercised without a page; what is under test is the mining, which is arithmetic over
outcomes and not a property of any destination.

    INVENTED  a guard nothing failed for                    must be 0
    MISSED    a condition every failure shared, not found   must be 0
"""

from __future__ import annotations

import sys

from factory.capability.failures import always_fails, guards
from factory.capability.variations import read
from factory.core.evidence import Did


def answered(*steps: tuple[bool, str]) -> list[dict]:
    """What a drafted capability returns: each act's Did, in order."""
    return [Did(ok=ok, detail=why).model_dump(mode="json") for ok, why in steps]


HELD = ((True, "went"), (True, "wrote"), (True, "pressed"))
BLANK = ((True, "went"), (True, "wrote"), (False, "refused: covered DIV"))


def run() -> int:
    invented = missed = failed = 0

    def check(name: str, ok: bool, detail: str) -> None:
        nonlocal failed
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name:52} {detail}")

    # V1 -- an attempt reads its own outcome from what came back.
    good = read("'ada'", answered(*HELD))
    stopped = read("''", answered(*BLANK))
    check("V1 a held run is held", good.held and good.stopped_at is None, good.line())
    check("V1 and a stopped one says where", not stopped.held and stopped.stopped_at == 2,
          stopped.line())

    # V2 -- one that never answered is not a failure of the input.
    silent = read("'x'", None)
    check("V2 answering nothing is not a page telling us something",
          not silent.held and silent.stopped_at is None, silent.line())

    # V3 -- SUCCESSES ALONE PRODUCE NO GUARDS. That is the finding, stated as a test.
    only_good = [read(f"'name{n}'", answered(*HELD)) for n in range(4)]
    invented += len(guards(only_good))
    check("V3 four successes produce no guards", not guards(only_good),
          f"{len(guards(only_good))} guards from 4 held runs")

    # V4 -- two failures agreeing do.
    mixed = [*only_good[:2], read("''", answered(*BLANK)),
             read("'   '", answered(*BLANK))]
    found = guards(mixed)
    missed += not found
    check("V4 two failures agreeing make a guard", len(found) == 1,
          found[0].line() if found else "none found")

    # V5 -- one failure is a coincidence, not a rule.
    once = [*only_good[:2], read("''", answered(*BLANK))]
    invented += len(guards(once))
    check("V5 a single failure is not yet a rule", not guards(once),
          f"{len(guards(once))} guards from 1 failure")

    # V6 -- a step no success ever reached is not a guard, it is a broken capability.
    early = ((False, "refused: no match"),)
    never = [read(f"'{n}'", answered(*early)) for n in range(3)]
    invented += len(guards(never))
    check("V6 always stopping is not a condition to check", not guards(never),
          f"{len(guards(never))} guards, always_fails={always_fails(never)}")
    check("V6 and that is told apart from a guard", always_fails(never), "refuse the candidate")

    # V7 -- the guard names the inputs it happened for, so a person can check the story.
    check("V7 a guard carries the inputs it came from",
          found and set(found[0].inputs) == {"''", "'   '"}, str(found[0].inputs))

    print(f"\nINVENTED a guard nothing failed for       : {invented}   (must be 0)")
    print(f"MISSED   a shared condition not found     : {missed}   (must be 0)")
    print(f"FAILED   cases not matching               : {failed}")
    return 1 if invented or missed or failed else 0


if __name__ == "__main__":
    sys.exit(run())
