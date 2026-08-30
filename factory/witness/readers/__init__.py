"""The socket. A reader is discovered, never imported by name.

Adding a surface must not edit this package. `discover()` reads the entry point group, and
`Ladder` takes its readers as an argument -- so an eval, or the thing that manufactures
readers, supplies its own without a back door being cut here for it.

A reader is PRODUCT, not machinery. One hand-written per surface kind is the same mistake
as one capability per workflow; if this package ends up importing them by name, perception
stopped being extendable at the point this driver exists to extend it.
"""

from __future__ import annotations

from importlib.metadata import entry_points
from typing import Protocol, runtime_checkable

from factory.core.contract import Contract, Reading
from factory.core.evidence import Did
from factory.witness.channel import Channel

GROUP = "factory.witness.readers"


@runtime_checkable
class Reader(Protocol):
    """Turns evidence into what it could see of it.

    `channel` is what makes a reader admissible at all: one reading a channel we authored
    is refused by the ladder before it is asked to read anything, however good it is.
    """

    name: str
    channel: Channel

    def read(self, did: Did, contract: Contract) -> Reading: ...


def discover() -> tuple[Reader, ...]:
    """Every reader registered at the entry point group.

    A reader that cannot be loaded raises here rather than being skipped: one silently
    missing from the ladder lowers coverage without lowering anybody's confidence.
    """
    return tuple(point.load()() for point in entry_points(group=GROUP))
