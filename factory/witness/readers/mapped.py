"""Reads fields the shape of a body hid, at paths learned from an act nobody could check.

WHAT MAKES IT ADMISSIBLE IS WHAT MAKES `Fetched` ADMISSIBLE: it reads a response the page
requested for itself, so the bytes are the server's and the server took no part in the act.
The mapping changes where it looks, never who wrote what it looks at.

NOT DISCOVERED, SUPPLIED. `readers/__init__.discover()` builds a reader with no arguments,
and this one is nothing without its mapping. `Ladder` takes its readers as an argument for
exactly this -- the note there says so -- so the composition root hands it one built from
what memory holds, and no back door is cut in the socket.

BLINDNESS IS STILL BLINDNESS. `readable` is the set of fields this mapping can actually
address in THIS body, not the set it was built with. A path that is no longer there refuses
as blind rather than as a refutation: the destination changed shape, which is not the same
as the destination disagreeing.
"""

from __future__ import annotations

import json
from typing import Any

from factory.core.contract import Contract, Reading
from factory.core.evidence import Did
from factory.witness.channel import Channel


def _at(body: Any, path: tuple[str, ...]) -> list[str]:
    """Every value this path reaches. A list on the way is walked, never indexed.

    A path is learned without the row it came from -- see `witness/learn._paths` -- so one
    path over a record set reaches one value per record, and all of them are returned.
    """
    reached: list[Any] = [body]
    for key in path:
        stepped: list[Any] = []
        for held in reached:
            if isinstance(held, list):
                stepped.extend(item.get(key) for item in held if isinstance(item, dict))
            elif isinstance(held, dict) and key in held:
                stepped.append(held[key])
        reached = [item for item in stepped if item is not None]
    return [str(item) for item in reached if not isinstance(item, (dict, list))]


class Mapped:
    """One reading, at paths somebody's own traffic taught us."""

    name = "mapped"
    channel = Channel.WIRE

    def __init__(self, paths: dict[str, tuple[str, ...]] | None = None) -> None:
        #: Empty is a state: a surface nothing has been learned about yet reads nothing and
        #: says so, which is what the ladder needs to fall past it.
        self.paths = paths or {}

    def read(self, did: Did, contract: Contract) -> Reading:
        bodies = []
        for exchange in did.exchanges:
            if not exchange.body:
                continue
            try:
                bodies.append(json.loads(exchange.body))
            except (ValueError, TypeError):
                continue

        values: dict[str, str] = {}
        readable: set[str] = set()
        for field, path in self.paths.items():
            found = [seen for body in bodies for seen in _at(body, path)]
            if not found:
                continue
            readable.add(field)
            want = contract.expects.get(field)
            #: The value it was asked about if it is there, and otherwise the first. A
            #: reader that only ever reported the first row would refute every record set
            #: whose order is not ours to control.
            values[field] = want if want in found else found[0]
        return Reading(values=values, readable=frozenset(readable))
