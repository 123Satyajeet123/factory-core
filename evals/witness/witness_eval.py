"""Does a verdict mean anything, and what does the ladder refuse?

    uv run python -m evals.witness.witness_eval

No browser, no network, no site, and no reader from this tree. Every reader below is
defined here and handed to the Ladder, which is the W7 claim demonstrated rather than
asserted: nothing in `witness/` was edited to admit them.

Scored two ways and both are reported. See gates/witness-verdict.md.

    FALSE CONFIRMED   confirmed when the effect did not happen     must be 0
    BLIND             unverifiable when it plainly did happen      budgeted, not 0

A witness that never confirms scores a perfect 0 on the first and is worth nothing, which
is why the second is printed beside it and a release may not trade one for the other.
"""

from __future__ import annotations

import sys

from factory.core.contract import Contract, Found, Verdict
from factory.core.evidence import Did
from factory.witness.channel import Channel
from factory.witness.ladder import Ladder

#: What a step claimed would be true. Two fields, so a partial read is distinguishable
#: from a complete one.
CLAIMED = Contract(binds={"id": "77", "status": "approved"})
BOTH = frozenset({"id", "status"})


class Says:
    """A reader that answers from a fixture, and admits what it could not look at."""

    def __init__(self, name: str, channel: Channel,
                 values: dict[str, str], saw: frozenset[str]) -> None:
        self.name, self.channel = name, channel
        self._values, self._saw = values, saw

    def read(self, did: Did, contract: Contract) -> Found:
        return Found(values=dict(self._values), saw=self._saw)


TRUTH = {"id": "77", "status": "approved"}
STALE = {"id": "77", "status": "pending"}

#: name, readers, contract, expected verdict, expected rung (None = do not care).
CASES = (
    ("wire agrees",
     [Says("fetched", Channel.WIRE, TRUTH, BOTH)], CLAIMED, Verdict.CONFIRMED, "fetched"),

    ("W5 the step did nothing",
     [Says("fetched", Channel.WIRE, STALE, BOTH)], CLAIMED, Verdict.REFUTED, "fetched"),

    ("corrupt: a bound field is absent, and the reader looked",
     [Says("fetched", Channel.WIRE, {"id": "77"}, BOTH)], CLAIMED, Verdict.REFUTED, "fetched"),

    ("render-only: the DOM agrees, and the DOM is ours",
     [Says("serialised", Channel.DOM, TRUTH, BOTH)], CLAIMED, Verdict.UNVERIFIABLE, None),

    ("injected: a reader on the channel that performed the act",
     [Says("echo", Channel.DISPATCH, TRUTH, BOTH)], CLAIMED, Verdict.UNVERIFIABLE, None),

    ("blind rung falls through to one that can see",
     [Says("asked", Channel.DESTINATION, {"id": "77"}, frozenset({"id"})),
      Says("fetched", Channel.WIRE, TRUTH, BOTH)], CLAIMED, Verdict.CONFIRMED, "fetched"),

    ("a lower rung never overrides a higher one",
     [Says("asked", Channel.DESTINATION, STALE, BOTH),
      Says("fetched", Channel.WIRE, TRUTH, BOTH)], CLAIMED, Verdict.REFUTED, "asked"),

    ("a reader that saw nothing confirms nothing",
     [Says("empty", Channel.WIRE, {}, frozenset())], CLAIMED, Verdict.UNVERIFIABLE, "empty"),

    ("no readers at all",
     [], CLAIMED, Verdict.UNVERIFIABLE, None),

    ("a contract that binds nothing cannot be satisfied",
     [Says("fetched", Channel.WIRE, TRUTH, BOTH)], Contract(), Verdict.UNVERIFIABLE, "fetched"),
)


def run() -> int:
    did = Did(ok=True, detail="the act, already performed")
    false_confirmed = blind = wrong_rung = mismatch = 0
    unverifiable = 0

    for name, readers, contract, expected, expected_rung in CASES:
        ladder = Ladder(readers=readers)
        receipt = ladder.witness(did, contract)

        ok = receipt.verdict is expected
        if not ok:
            mismatch += 1
        if receipt.verdict is Verdict.CONFIRMED and expected is not Verdict.CONFIRMED:
            false_confirmed += 1
        if receipt.verdict is Verdict.UNVERIFIABLE and expected is Verdict.CONFIRMED:
            blind += 1
        if expected_rung is not None and receipt.rung != expected_rung:
            wrong_rung += 1
            ok = False
        if receipt.verdict is Verdict.UNVERIFIABLE:
            unverifiable += 1

        print(f"{'ok  ' if ok else 'FAIL'} {name:48} {receipt.verdict:<13} "
              f"rung={receipt.rung or '-':<11} refused={len(ladder.refused())} "
              f"{receipt.why}")

    print(f"\nFALSE CONFIRMED  confirmed when it did not happen  : {false_confirmed}   (must be 0)")
    print(f"BLIND            unverifiable when it did happen    : {blind}")
    print(f"RUNG             decided by the wrong rung          : {wrong_rung}   (must be 0)")
    print(f"VERDICT          not the expected verdict           : {mismatch}   (must be 0)")
    print(f"W4               unverifiable, as a fraction        : "
          f"{unverifiable}/{len(CASES)}")
    return 1 if false_confirmed or blind or wrong_rung or mismatch else 0


if __name__ == "__main__":
    sys.exit(run())
