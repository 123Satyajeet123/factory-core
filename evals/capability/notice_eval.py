"""Does a burst of demonstrations read as a habit?

    uv run python -m evals.capability.notice_eval

No browser and no site. Synthetic segments with real timestamps, because the whole rule is
about time and a fixture that fakes the clock cannot test it.

    CREDULOUS  one afternoon read as corroboration    must be 0
    DEAF       a real habit was not noticed           must be 0
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta

from factory.capability.notice import SITTING, across, sittings, when
from factory.core.ledger import Act, Segment, Whose
from factory.core.verbs import Doing

START = datetime(2026, 8, 24, 9, 0, tzinfo=UTC)


def shown(*offsets: timedelta, whose: Whose = Whose.PERSON) -> list[Segment]:
    """One segment per offset, each carrying a real act at that time."""
    return [Segment(whose=whose, acts=[Act(doing=Doing.PRESS, at=START + off)])
            for off in offsets]


MINUTES = [timedelta(minutes=m) for m in (0, 3, 7, 11, 19, 26, 34, 41, 50, 58)]
DAYS = [timedelta(days=d) for d in (0, 1, 4)]


def run() -> int:
    credulous = deaf = failed = 0

    def check(name: str, ok: bool, detail: str) -> None:
        nonlocal failed
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name:48} {detail}")

    # N1 -- the finding this rule comes from: a burst is one experiment.
    burst = across("an afternoon", shown(*MINUTES))
    credulous += bool(burst)
    check("N1 ten demonstrations in one hour is not a habit", not burst, burst.why())

    # N2 -- and coming back is.
    habit = across("a habit", shown(*DAYS))
    deaf += not habit
    check("N2 three, on three days, is", bool(habit), habit.why())

    # N3 -- the boundary is the gap, not the count. Two beats ten.
    two = across("twice", shown(timedelta(0), timedelta(days=1)))
    check("N3 two sittings beat ten repetitions", bool(two) and not burst,
          f"2 demos -> {two.sittings} sittings; 10 demos -> {burst.sittings}")

    # N4 -- what the factory drove is not evidence of anything but itself.
    ours = across("ours", shown(*DAYS, whose=Whose.FACTORY))
    credulous += bool(ours)
    check("N4 the factory cannot corroborate itself", not ours, ours.why())

    # N5 -- a segment with no acts has no time, and says so.
    blind = across("undated", [Segment(), Segment()])
    check("N5 undated is counted, never guessed",
          not blind and blind.undated == 2, blind.why())

    # N6 -- what the one knob admits, reported rather than asserted.
    print("\n  gap        an afternoon (10 in 1h)   three days apart")
    for hours in (1, 6, 24, 72):
        gap = timedelta(hours=hours)
        a = sittings(shown(*MINUTES), gap)
        b = sittings(shown(*DAYS), gap)
        print(f"  {hours:>3}h       {a} sittings                {b} sittings")
    #: The value is not asserted -- a constant equalling its own literal checks nothing.
    #: What is asserted is that the shipped one separates the two cases above.
    check("N6 the shipped gap separates the two",
          sittings(shown(*MINUTES), SITTING) == 1 and sittings(shown(*DAYS), SITTING) == 3,
          f"SITTING = {SITTING}")

    # N7 -- time comes from the act, not from anywhere else.
    one = shown(timedelta(days=2))[0]
    check("N7 a segment happens when its first act did",
          when(one) == START + timedelta(days=2), f"{when(one)}")

    print(f"\nCREDULOUS one afternoon read as corroboration : {credulous}   (must be 0)")
    print(f"DEAF      a real habit was not noticed         : {deaf}   (must be 0)")
    print(f"FAILED    cases not matching                   : {failed}")
    return 1 if credulous or deaf or failed else 0


if __name__ == "__main__":
    sys.exit(run())
