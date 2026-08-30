from __future__ import annotations

import sys

from factory.capability.evidence import admissible, confidence, disagreed, one_per_reader
from factory.core.contract import Receipt, Verdict


def said(reader: str, verdict: Verdict, channel: str = "wire") -> Receipt:
    return Receipt(verdict=verdict, reader=reader, channel=channel)


CONFIRMED, REFUTED, UNVERIFIABLE = Verdict.CONFIRMED, Verdict.REFUTED, Verdict.UNVERIFIABLE


def run() -> int:
    inflated = dropped = failed = 0

    def check(name: str, ok: bool, detail: str) -> None:
        nonlocal failed
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name:48} {detail}")

    same = [said("asked", CONFIRMED) for _ in range(5)]
    inflated += len(one_per_reader(same)) - 1
    check("E1 one reader is one unit", len(one_per_reader(same)) == 1,
          f"5 receipts from one reader -> {len(one_per_reader(same))}")

    two = [said("asked", CONFIRMED), said("fetched", CONFIRMED)]
    dropped += 2 - len(one_per_reader(two))
    check("E2 two readers are two units", len(one_per_reader(two)) == 2,
          f"{confidence(two).confirmed} confirmed")

    blind = [said("asked", CONFIRMED), said("fetched", UNVERIFIABLE)]
    inflated += confidence(blind).receipts - 1
    check("E3 unverifiable is not evidence", confidence(blind).receipts == 1,
          f"{confidence(blind).receipts} receipts from 2 verdicts")

    unnamed = [Receipt(verdict=CONFIRMED)]
    inflated += len(admissible(unnamed))
    check("E4 a receipt naming no reader counts for nothing",
          not admissible(unnamed), f"{len(admissible(unnamed))} admissible")

    split = [said("asked", CONFIRMED), said("fetched", REFUTED)]
    counted = confidence(split)
    check("E5 disagreement is kept, not resolved",
          disagreed(split) and (counted.confirmed, counted.refuted) == (1, 1),
          f"confirmed={counted.confirmed} refuted={counted.refuted}")

    check("E6 caused is a subset of confirmed, never invented",
          confidence(two, caused=True).caused == 2 and confidence(two).caused == 0,
          f"{confidence(two, caused=True).caused} caused of {confidence(two).confirmed}")

    print(f"\nINFLATED evidence counted more than once : {inflated}   (must be 0)")
    print(f"DROPPED  independent evidence not counted : {dropped}   (must be 0)")
    print(f"FAILED   cases not matching               : {failed}")
    return 1 if inflated or dropped or failed else 0


if __name__ == "__main__":
    sys.exit(run())
