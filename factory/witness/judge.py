"""One rung's reading, turned into a verdict.

ORDER OF CHECKS IS THE POINT. Blindness is asked before disagreement, because a reader that
could not see a field has not disagreed about it -- and asking the other way round turns
every blind rung into a refutation, which promotes nothing and demotes everything.
"""

from __future__ import annotations

from factory.core.contract import Contract, Found, Receipt, Verdict
from factory.witness.blind import unseen


def judge(contract: Contract, found: Found, *, rung: str = "", channel: str = "") -> Receipt:
    """What this reading says about this contract, and nothing about any other rung."""
    where = {"rung": rung, "channel": channel}

    if not contract.binds:
        return Receipt(verdict=Verdict.UNVERIFIABLE, why="contract binds nothing", **where)

    blind_to = unseen(contract, found)
    if blind_to:
        return Receipt(verdict=Verdict.UNVERIFIABLE, unseen=blind_to,
                       why=f"cannot see {', '.join(sorted(blind_to))}", **where)

    disagreed = frozenset(
        field for field, want in contract.binds.items() if found.values.get(field) != want)
    if disagreed:
        return Receipt(verdict=Verdict.REFUTED, disagreed=disagreed,
                       why=f"differs on {', '.join(sorted(disagreed))}", **where)

    return Receipt(verdict=Verdict.CONFIRMED, why=f"{len(contract.binds)} bound", **where)
