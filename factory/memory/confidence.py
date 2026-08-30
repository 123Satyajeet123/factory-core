"""How much evidence an entry has, as a bound rather than a count.

Settled in gates/promotion-threshold.md. "Three in a row" promotes noise and "twenty in a
row" never promotes, and both numbers would have been picked rather than derived. The lower
bound of a Wilson interval carries one meaning -- how sure we insist on being -- and sample
size stops being a separate knob, because with a perfect record the bound is n / (n + z^2):

    3 / 3    0.44        12 / 12   0.76        30 / 30   0.89

Only witness receipts count. A refutation is evidence in the same arithmetic, so it moves
the bound down rather than merely blocking promotion.
"""

from __future__ import annotations

import math

from factory.core.memory import Confidence

#: 95%. Wider insists on more evidence before anything moves.
Z = 1.96


def bound(confidence: Confidence) -> float:
    """The lower bound of the Wilson interval on this entry's success rate."""
    n = confidence.receipts
    if n == 0:
        return 0.0
    seen = confidence.confirmed / n
    middle = seen + Z * Z / (2 * n)
    spread = Z * math.sqrt(seen * (1 - seen) / n + Z * Z / (4 * n * n))
    return max(0.0, (middle - spread) / (1 + Z * Z / n))


def _self_check() -> None:
    """uv run python -m factory.memory.confidence"""
    perfect = [(n, bound(Confidence(confirmed=n))) for n in (3, 12, 30)]
    for n, got in perfect:
        assert abs(got - n / (n + Z * Z)) < 1e-9, f"perfect record is n/(n+z^2) at {n}"
    assert perfect[0][1] < perfect[1][1] < perfect[2][1], "more evidence, higher bound"
    assert bound(Confidence()) == 0.0, "no receipts, no confidence"

    one_bad = bound(Confidence(confirmed=11, refuted=1))
    assert one_bad < perfect[1][1], "a refutation moves the bound down"
    assert bound(Confidence(confirmed=1, refuted=1)) < bound(Confidence(confirmed=12)), \
        "a coin flip never outranks a record"
    print("confidence:", {n: round(b, 2) for n, b in perfect},
          "| 11/12 with one refuted:", round(one_bad, 2))


if __name__ == "__main__":
    _self_check()
