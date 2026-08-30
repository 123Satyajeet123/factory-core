"""Is the socket a socket, or does perception stop where this tree does?

    uv run python -m evals.witness.socket_eval

W7 in gates/witness-verdict.md. A reader published from outside `factory/` must reach a
verdict with no import added to a ladder, no branch on a surface kind and no entry in a
list. `evals/witness/outside/` is that reader: a separate package declaring an entry point,
installed like anything the factory will later manufacture.

Nothing under `factory/witness/` is edited by this eval. If it ever has to be, the socket
was never one.
"""

from __future__ import annotations

import sys

from factory.core.contract import Contract, Verdict
from factory.core.evidence import Did, Exchange
from factory.witness.ladder import Ladder
from factory.witness.readers import discover
from factory.witness.readers.fetched import Fetched

RECORDS = '[{"id": "883973", "name": "Ada Lovelace"}]'
RECEIPT = "sent_at=2026-08-30T09:15:00Z\nstatus=delivered"


def did(*bodies: tuple[str, str]) -> Did:
    return Did(ok=True, exchanges=[
        Exchange(url="/x", status=200, content_type=kind, size=len(body), body=body)
        for kind, body in bodies])


EVIDENCE = did(("application/json", RECORDS), ("text/plain", RECEIPT))
DELIVERED = Contract(expects={"sent_at": "2026-08-30T09:15:00Z"})
MISDELIVERED = Contract(expects={"sent_at": "1999-01-01T00:00:00Z"})


def main() -> int:
    faults = 0
    outside = discover()
    names = sorted(r.name for r in outside)
    print(f"discovered through the entry point group : {names}")
    if "receipted" not in names:
        faults += 1
        print("FAULT the outside reader was not discovered")
    if "fetched" not in names:
        faults += 1
        print("FAULT the reference reader does not come through the socket either")

    ranked = [r.name for r in Ladder(outside).admissible()]
    print(f"admissible, best evidence first          : {ranked}")
    if ranked and ranked[0] != "receipted":
        faults += 1
        print("FAULT a destination reader must outrank a wire reader")

    blind = Ladder((Fetched(),)).witness(EVIDENCE, DELIVERED)
    print(f"wire reader alone                        : {blind.verdict} ({blind.why})")
    if blind.verdict is not Verdict.UNVERIFIABLE:
        faults += 1
        print("FAULT the wire reader cannot see sent_at and must say so")

    extended = Ladder(outside).witness(EVIDENCE, DELIVERED)
    print(f"with the outside reader admitted         : {extended.verdict} "
          f"by {extended.reader!r} on {extended.channel!r}")
    if extended.verdict is not Verdict.CONFIRMED or extended.reader != "receipted":
        faults += 1
        print("FAULT admitting a reader did not extend what can be witnessed")

    #: W8. The best rung refutes; the rung below is blind and would answer UNVERIFIABLE.
    #: Walking on after a refutation is how a system talks itself into an answer.
    stopped = Ladder(outside).witness(EVIDENCE, MISDELIVERED)
    print(f"best rung refutes, lower rung is blind   : {stopped.verdict} "
          f"by {stopped.reader!r}")
    if stopped.verdict is not Verdict.REFUTED:
        faults += 1
        print("FAULT the ladder walked past a refutation")

    print(f"\nFAULTS  ways the socket is not a socket : {faults}   (must be 0)")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(main())
