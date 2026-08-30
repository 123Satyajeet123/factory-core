"""A reader the tree does not know about, on a channel the tree does not read.

It answers about `sent_at`, which the WIRE reader is blind to, so admitting it turns an
UNVERIFIABLE into a verdict -- which is what "perception is extendable" has to mean if it
means anything.

Deliberately minimal. The point under test is the socket, not this reader's quality; it must
pass the same suite as anything else, which is why it refuses what it cannot see rather than
reporting a value it did not read.
"""

from __future__ import annotations

from typing import Any

MINE = frozenset({"sent_at"})


class Receipted:
    """Reads a delivery receipt the destination issued."""

    name = "receipted"
    #: Ranked above WIRE by factory.witness.channel.QUALITY.
    channel = "destination"

    def read(self, did: Any, contract: Any) -> Any:
        from factory.core.contract import Reading

        seen: dict[str, str] = {}
        for exchange in did.exchanges:
            for line in (exchange.body or "").splitlines():
                if line.startswith("sent_at="):
                    seen["sent_at"] = line.split("=", 1)[1].strip()
        return Reading(values={k: v for k, v in seen.items() if k in contract.expects},
                       readable=MINE)
