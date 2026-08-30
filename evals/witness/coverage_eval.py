"""What is the ceiling on promotion, and which reader would raise it most?

    uv run python -m evals.witness.coverage_eval

W4 in gates/witness-verdict.md. `unverifiable` moves neither side of the Wilson arithmetic,
so an act nobody could check is invisible to promotion. This is the edge it otherwise does
not have: counted by the SHAPE of surface that defeated it, the number says what to build.

No browser and no site. The shapes below are the ones a real run meets.
"""

from __future__ import annotations

import json
import sys

from factory.core.contract import Contract
from factory.core.evidence import Did, Exchange
from factory.witness.coverage import Blocked, tally
from factory.witness.ladder import Ladder
from factory.witness.readers.fetched import Fetched

LANDED = Contract(expects={"id": "883973"})
SENT = Contract(expects={"sent_at": "2026-08-30T09:15:00Z"})


def did(*bodies: tuple[str, str]) -> Did:
    return Did(ok=True, exchanges=[
        Exchange(url="/x", status=200, content_type=kind, size=len(body), body=body)
        for kind, body in bodies])


JSON_ROWS = ("application/json", json.dumps([{"id": "883973"}, {"id": "883974"}]))
PAINTED = ("text/html", "<canvas></canvas>")

#: A run of eight acts across four shapes of surface, which is what a real one looks like.
RUN = (
    (did(JSON_ROWS), LANDED),          # confirmed
    (did(JSON_ROWS), LANDED),          # confirmed
    (did(("application/json", json.dumps([{"id": "999"}]))), LANDED),   # refuted
    (Did(ok=True), LANDED),            # fetched nothing
    (did(PAINTED), LANDED),            # paints only
    (did(PAINTED), LANDED),            # paints only
    (did(PAINTED), LANDED),            # paints only
    (did(JSON_ROWS), SENT),            # structured, field not in it
)


def main() -> int:
    ladder = Ladder((Fetched(),))
    coverage = tally((evidence, ladder.witness(evidence, contract))
                     for evidence, contract in RUN)

    print(f"acts {coverage.acts}   confirmed {coverage.confirmed}   "
          f"refuted {coverage.refuted}   unverifiable {coverage.unverifiable}")
    print(f"ceiling on promotion  {coverage.ceiling:.0%}   "
          f"(the rest could never be promoted, however cheap it got)\n")

    for key, demand in sorted(coverage.demand.items(), key=lambda kv: -kv[1].acts):
        print(f"  {demand.acts} acts  {key}"
              + (f"  fields={sorted(demand.fields)}" if demand.fields else ""))

    worst = coverage.worst()
    print(f"\nbuild this reader first: {worst.blocked} "
          f"for {list(worst.offered) or 'nothing fetched'}")

    faults = 0
    if coverage.ceiling != 3 / 8:
        faults += 1
        print("FAULT the ceiling is not the fraction that reached a verdict")
    if worst.blocked is not Blocked.PAINTS_ONLY:
        faults += 1
        print("FAULT the shape blocking the most acts is not the one named")
    #: The demand signal must survive being right for the wrong reason: a run with nothing
    #: unverifiable has no demand, and a ceiling of 100%.
    clean = tally([(did(JSON_ROWS), ladder.witness(did(JSON_ROWS), LANDED))])
    if clean.demand or clean.ceiling != 1.0:
        faults += 1
        print("FAULT a fully witnessed run still reported demand")

    print(f"\nFAULTS  {faults}   (must be 0)")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(main())
