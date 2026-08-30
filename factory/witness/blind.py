
from __future__ import annotations

from factory.core.contract import Contract, Reading


def unreadable(contract: Contract, reading: Reading) -> frozenset[str]:
    return frozenset(contract.expects) - reading.readable
