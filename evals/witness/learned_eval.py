"""Can perception be extended without editing this package?

    uv run python -m evals.witness.learned_eval

`witness/readers/__init__.py` claims a reader is PRODUCT, not machinery, and that one
hand-written per surface kind is the same mistake as one capability per workflow. Until
something produced one, that was a promise. This is the check on the promise.

WHAT IS PRODUCED IS A MAPPING, NOT A PROGRAM. So the questions are not "does the generated
code run" but the ones that decide whether learning is safe: does it learn only from
equality against a value we expected, does an unlearned surface stay blind rather than
confirm, and does a mapping that stops resolving refuse as blindness rather than as a
refutation.

FALSE CONFIRMED IS STILL THE GATE. A reader that learns is a reader that can learn wrong,
and the whole ladder is worth nothing if learning is the way a false confirmation gets in.
"""

from __future__ import annotations

import json
import sys

from factory.core.contract import Contract, Verdict
from factory.core.evidence import Did, Exchange
from factory.witness.ladder import Ladder
from factory.witness.learn import mapping, merged
from factory.witness.readers.fetched import Fetched
from factory.witness.readers.mapped import Mapped

#: The field is there. It is not called what the contract calls it, and it is two envelopes
#: down -- which is an ordinary shape and the one `Fetched` cannot address.
NESTED = {"data": {"result": [{"id": "9", "customer": {"full_name": "Ada Lovelace"}}]}}
WANTED = Contract(expects={"name": "Ada Lovelace"})


def did(body: object) -> Did:
    return Did(ok=True, exchanges=[Exchange(url="/api", status=200,
                                            content_type="application/json",
                                            body=json.dumps(body))])


def verdict(readers: list[object], evidence: Did, contract: Contract = WANTED) -> Verdict:
    return Ladder(readers).witness(evidence, contract).verdict


def main() -> int:
    false_confirmed = 0
    faults = 0
    seen = did(NESTED)

    #: 1. The state before anything is learned. Some reader must say it cannot see this,
    #: and none may say it is confirmed.
    before = verdict([Fetched()], seen)
    print(f"unlearned, hand-written reader   {before}")
    if before is not Verdict.UNVERIFIABLE:
        faults += 1
        false_confirmed += before is Verdict.CONFIRMED
        print("  FAULT a nested field under another name was not reported as unreadable")

    #: 2. What the act taught. Equality against a value the contract expected, nothing else.
    learned = mapping(WANTED, seen)
    print(f"learned from the same act        {dict(learned)}")
    if learned.get("name") != ("data", "result", "customer", "full_name"):
        faults += 1
        print("  FAULT the path to the expected value was not derived")

    #: 3. The second run of the same surface, with what the first taught.
    after = verdict([Fetched(), Mapped(learned)], seen)
    print(f"the run after                    {after}")
    if after is not Verdict.CONFIRMED:
        faults += 1
        print("  FAULT a surface that taught us where to look still cannot be read")

    #: 4. THE GATE. A destination that disagrees must still refute through a learned path.
    other = did({"data": {"result": [{"id": "9",
                                      "customer": {"full_name": "Grace Hopper"}}]}})
    said = verdict([Mapped(learned)], other)
    print(f"the destination disagrees        {said}")
    if said is not Verdict.REFUTED:
        faults += 1
        false_confirmed += said is Verdict.CONFIRMED
        print("  FAULT a learned reader could not refute")

    #: 5. Nothing is learned from a body that never carried the value. This is where a
    #: false confirmation would be manufactured rather than merely missed.
    absent = mapping(WANTED, did({"data": {"result": [{"id": "9"}]}}))
    print(f"learned from a body without it   {dict(absent) or '{}'}")
    if absent:
        faults += 1
        print("  FAULT a path was learned for a value that was never there")

    #: 6. A mapping whose path stopped resolving is BLIND, not a refutation. The shape
    #: changing and the destination disagreeing are opposite answers.
    moved = verdict([Mapped(learned)], did({"data": {"rows": [{"full_name": "Ada"}]}}))
    print(f"the shape moved underneath       {moved}")
    if moved is not Verdict.UNVERIFIABLE:
        faults += 1
        false_confirmed += moved is Verdict.CONFIRMED
        print("  FAULT a path that no longer resolves was treated as disagreement")

    #: 7. An empty mapping reads nothing. A manufactured reader that confirms before it has
    #: learned anything is the laziest possible wrong answer.
    fresh = verdict([Mapped()], seen)
    print(f"a reader that learned nothing    {fresh}")
    if fresh is not Verdict.UNVERIFIABLE:
        faults += 1
        false_confirmed += fresh is Verdict.CONFIRMED
        print("  FAULT an unlearned reader answered")

    #: 8. A field the body already calls by the contract's own name teaches NOTHING. The
    #: hand-written reader would have found it, so a mapping entry for it would be a
    #: mapping that says nothing -- and a store full of those is how a learned reader
    #: starts looking like it knows more than it does.
    already = mapping(Contract(expects={"id": "9"}), seen)
    print(f"a field already readable         {dict(already) or '{}'}")
    if already:
        faults += 1
        print("  FAULT a path was learned for a field no reader was ever blind to")

    #: 9. Two acts, two lessons, and neither lost.
    renamed = mapping(Contract(expects={"reference": "9"}), seen)
    both = merged(learned, renamed)
    print(f"merged across acts               {sorted(both)}")
    if sorted(both) != ["name", "reference"]:
        faults += 1
        print("  FAULT a later lesson replaced an earlier one instead of joining it")

    print(f"\nFALSE CONFIRMED  learning made a wrong verdict : {false_confirmed}   (must be 0)")
    print(f"FAULTS           {faults}")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(main())
