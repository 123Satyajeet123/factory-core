"""A reader that cannot see an expected field refuses.

"Looked and it was not there" and "cannot look at this kind of thing at all" are the same
absence in the bytes and opposite answers. The first refutes. The second is blindness, and
returning anything but UNVERIFIABLE for it lets a reader that sees almost nothing confirm
almost everything.
"""

from __future__ import annotations

from factory.core.contract import Contract, Reading


def unreadable(contract: Contract, reading: Reading) -> frozenset[str]:
    """Expected fields this reader could not address at all."""
    return frozenset(contract.expects) - reading.readable
