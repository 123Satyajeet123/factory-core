"""One reader's reading, turned into a verdict.

ORDER OF CHECKS IS THE POINT. Blindness is asked before disagreement, because a reader that
could not see a field has not disagreed about it -- and asking the other way round turns
every blind reader into a refutation, which promotes nothing and demotes everything.
"""

from __future__ import annotations

from factory.core.contract import Contract, Reading, Receipt, Verdict
from factory.witness.blind import unreadable


def judge(contract: Contract, reading: Reading, *,
          reader: str = "", channel: str = "") -> Receipt:
    """What this reading says about this contract, and nothing about any other reader."""
    source = {"reader": reader, "channel": channel}

    if not contract.expects:
        return Receipt(verdict=Verdict.UNVERIFIABLE, why="contract expects nothing", **source)

    blind_to = unreadable(contract, reading)
    if blind_to:
        return Receipt(verdict=Verdict.UNVERIFIABLE, unreadable=blind_to,
                       why=f"cannot see {', '.join(sorted(blind_to))}", **source)

    disagreed = frozenset(
        field for field, want in contract.expects.items() if reading.values.get(field) != want)
    if disagreed:
        return Receipt(verdict=Verdict.REFUTED, disagreed=disagreed,
                       why=f"differs on {', '.join(sorted(disagreed))}", **source)

    return Receipt(verdict=Verdict.CONFIRMED, why=f"{len(contract.expects)} fields", **source)
