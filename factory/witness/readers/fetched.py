"""Reads what the page fetched for itself. The WIRE rung.

ADMISSIBLE BECAUSE WE DID NOT AUTHOR IT. A click mutates the document, so the DOM carries
our own bytes back to us. A response the page requested carries the server's, and the server
did not take part in the act.

BINDS ON SHAPE, NEVER ON A SITE. It looks for lists of objects with shared keys anywhere in
a structured body, and falls back to CSV. There is no host table, no field map and no
selector, so the next destination costs nothing -- which is the difference between a reader
and a workflow.

WHAT IT SEES IS DERIVED, NOT DECLARED. `readable` is the set of keys the records actually
carried. A contract binding a field no record carries is refused as blindness rather than
guessed at, and nobody had to write down what this destination offers.

PRESENCE IS NOT CAUSATION, and this reader cannot tell them apart. It answers "a record
with these values is there", not "this act put it there". The contract is what carries the
difference: derived from the demonstration's delta, it binds what CHANGED.
"""

from __future__ import annotations

from factory.core.contract import Contract, Reading
from factory.core.evidence import Did
from factory.witness.channel import Channel


class Fetched:
    """One reading of one step's exchanges."""

    name = "fetched"
    channel = Channel.WIRE

    def read(self, did: Did, contract: Contract) -> Reading:
        records = [row for exchange in did.exchanges for row in exchange.records()]

        readable = frozenset().union(*(set(r) for r in records)) if records else frozenset()
        wanted = set(contract.expects)
        if not records or not wanted & readable:
            return Reading(readable=readable)

        #: The record agreeing on the most expected fields. Reporting the closest one is
        #: what lets `judge` name the fields that differ; picking one that agrees on
        #: everything and hiding the rest would confirm whatever was asked.
        best = max(records, key=lambda row: sum(
            row.get(field) == want for field, want in contract.expects.items()))
        return Reading(values={f: best[f] for f in wanted & set(best)}, readable=readable)
