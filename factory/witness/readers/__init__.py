
from __future__ import annotations

from importlib.metadata import entry_points
from typing import Protocol, runtime_checkable

from factory.core.contract import Contract, Reading
from factory.core.evidence import Did
from factory.witness.channel import Channel

GROUP = "factory.witness.readers"


@runtime_checkable
class Reader(Protocol):

    name: str
    channel: Channel

    def read(self, did: Did, contract: Contract) -> Reading: ...


def discover() -> tuple[Reader, ...]:
    return tuple(point.load()() for point in entry_points(group=GROUP))
