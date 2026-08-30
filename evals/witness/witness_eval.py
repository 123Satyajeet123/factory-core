"""Does a verdict mean anything, and what does the ladder refuse?

    uv run python -m evals.witness.witness_eval

No browser, no network, no site, and no reader from this tree. Every reader below is defined
here and handed to the Ladder, which demonstrates W7 rather than asserting it: nothing in
`witness/` was edited to admit them.

Scored two ways and both are reported. See gates/witness-verdict.md.

    FALSE CONFIRMED   confirmed when the effect did not happen     must be 0
    BLIND             unverifiable when it plainly did happen      budgeted, not 0

A witness that never confirms scores a perfect 0 on the first and is worth nothing, which is
why the second is printed beside it and a release may not trade one for the other.
"""

from __future__ import annotations

import sys

from factory.core.contract import Contract, Reading, Verdict
from factory.core.evidence import Did
from factory.witness.channel import Channel
from factory.witness.ladder import Ladder


class FixtureReader:
    """A reader that answers from a fixture, and admits what it could not read.

    `readable` is separate from `values` on purpose: it is how the suite tells a reader
    that looked and found nothing from one that cannot address the field at all.
    """

    def __init__(self, name: str, channel: Channel,
                 values: dict[str, str], readable: frozenset[str]) -> None:
        self.name, self.channel = name, channel
        self._values, self._readable = values, readable

    def read(self, did: Did, contract: Contract) -> Reading:
        return Reading(values=dict(self._values), readable=self._readable)


#: What the step claimed would be true afterwards. Two fields, so a partial read is
#: distinguishable from a complete one.
CONTRACT = Contract(expects={"id": "77", "status": "approved"})
ALL_FIELDS = frozenset({"id", "status"})

#: The world as the step claimed it, and as it was beforehand -- so "nothing happened" is a
#: fixture rather than a description.
AFTER = {"id": "77", "status": "approved"}
BEFORE = {"id": "77", "status": "pending"}


def wire(values: dict[str, str], readable: frozenset[str] = ALL_FIELDS) -> FixtureReader:
    return FixtureReader("fetched", Channel.WIRE, values, readable)


def destination(values: dict[str, str],
                readable: frozenset[str] = ALL_FIELDS) -> FixtureReader:
    return FixtureReader("asked", Channel.DESTINATION, values, readable)


#: name, readers, contract, expected verdict, expected reader (None = do not care).
CASES = (
    ("the wire agrees",
     [wire(AFTER)], CONTRACT, Verdict.CONFIRMED, "fetched"),

    ("W5 the step did nothing, and the contract expects real fields",
     [wire(BEFORE)], CONTRACT, Verdict.REFUTED, "fetched"),

    ("corrupt: an expected field is absent, and the reader looked",
     [wire({"id": "77"})], CONTRACT, Verdict.REFUTED, "fetched"),

    ("render-only: the DOM agrees, and the DOM is ours",
     [FixtureReader("serialised", Channel.DOM, AFTER, ALL_FIELDS)],
     CONTRACT, Verdict.UNVERIFIABLE, None),

    ("injected: a reader on the channel that performed the act",
     [FixtureReader("echo", Channel.DISPATCH, AFTER, ALL_FIELDS)],
     CONTRACT, Verdict.UNVERIFIABLE, None),

    ("a blind reader falls through to one that can see",
     [destination({"id": "77"}, frozenset({"id"})), wire(AFTER)],
     CONTRACT, Verdict.CONFIRMED, "fetched"),

    ("a lower reader never overrides a higher one",
     [destination(BEFORE), wire(AFTER)], CONTRACT, Verdict.REFUTED, "asked"),

    ("a reader that could read nothing confirms nothing",
     [wire({}, frozenset())], CONTRACT, Verdict.UNVERIFIABLE, "fetched"),

    ("no readers at all",
     [], CONTRACT, Verdict.UNVERIFIABLE, None),

    ("a contract that expects nothing cannot be satisfied",
     [wire(AFTER)], Contract(), Verdict.UNVERIFIABLE, "fetched"),
)


def run() -> int:
    did = Did(ok=True, detail="the act, already performed")
    false_confirmed = blind = wrong_reader = mismatch = unverifiable = 0

    for name, readers, contract, expected, expected_reader in CASES:
        ladder = Ladder(readers=readers)
        receipt = ladder.witness(did, contract)

        ok = receipt.verdict is expected
        if not ok:
            mismatch += 1
        if receipt.verdict is Verdict.CONFIRMED and expected is not Verdict.CONFIRMED:
            false_confirmed += 1
        if receipt.verdict is Verdict.UNVERIFIABLE and expected is Verdict.CONFIRMED:
            blind += 1
        if expected_reader is not None and receipt.reader != expected_reader:
            wrong_reader += 1
            ok = False
        if receipt.verdict is Verdict.UNVERIFIABLE:
            unverifiable += 1

        print(f"{'ok  ' if ok else 'FAIL'} {name:56} {receipt.verdict:<13} "
              f"by={receipt.reader or '-':<11} refused={len(ladder.inadmissible())} "
              f"{receipt.why}")

    print(f"\nFALSE CONFIRMED  confirmed when it did not happen : {false_confirmed}   (must be 0)")
    print(f"BLIND            unverifiable when it did happen   : {blind}")
    print(f"READER           decided by the wrong reader       : {wrong_reader}   (must be 0)")
    print(f"VERDICT          not the expected verdict          : {mismatch}   (must be 0)")
    print(f"W4               unverifiable, as a fraction       : {unverifiable}/{len(CASES)}")
    return 1 if false_confirmed or blind or wrong_reader or mismatch else 0


if __name__ == "__main__":
    sys.exit(run())
