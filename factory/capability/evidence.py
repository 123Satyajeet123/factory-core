from __future__ import annotations

from collections.abc import Iterable

from factory.core.contract import Receipt, Verdict
from factory.core.memory import Confidence

COUNTS = (Verdict.CONFIRMED, Verdict.REFUTED)


def admissible(receipts: Iterable[Receipt]) -> list[Receipt]:
    return [r for r in receipts if r.verdict in COUNTS and r.reader]


def one_per_reader(receipts: Iterable[Receipt]) -> list[Receipt]:
    first: dict[str, Receipt] = {}
    for receipt in admissible(receipts):
        first.setdefault(receipt.reader, receipt)
    return list(first.values())


def disagreed(receipts: Iterable[Receipt]) -> bool:
    verdicts = {r.verdict for r in one_per_reader(receipts)}
    return verdicts == set(COUNTS)


def confidence(receipts: Iterable[Receipt], *, caused: bool = False) -> Confidence:
    counted = one_per_reader(receipts)
    confirmed = sum(r.verdict is Verdict.CONFIRMED for r in counted)
    return Confidence(
        confirmed=confirmed,
        refuted=sum(r.verdict is Verdict.REFUTED for r in counted),
        caused=confirmed if caused else 0,
    )
