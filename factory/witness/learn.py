"""Where a field the contract wanted actually appeared, learned from an act nobody could check.

A READER IS A MAPPING, NOT A PROGRAM. `witness/readers/__init__.py` says a reader is
product and that one hand-written per surface kind is the same mistake as one capability
per workflow. The obvious reading of that is code generation -- draft a parser, install it,
run it. This is the smaller one: what a reader for a structured body actually differs in is
WHERE it looks, and where is data. So nothing is generated, nothing is installed, and no
model-authored code runs in this interpreter.

DERIVED FROM THE ACT, NOT FROM THE DESTINATION. The contract says the value should be
`Ada Lovelace`; the body carries `Ada Lovelace` under `customer.full_name`. That the two
are the same value is the whole evidence, and it is the same argument the rest of the tree
makes: the procedure is read out of the record, and so is the perception.

WHY THIS IS NOT A GUESS. `Fetched` already refuses a field it cannot address, so an act
reaches here only after some reader said UNVERIFIABLE. What is learned is only ever "the
value we expected was sitting at this path", never "this path probably means that field".
A path whose value merely resembles the expectation is not admitted: the comparison is
equality.

THE FIRST RUN CANNOT USE THIS AND THAT IS CORRECT. Learning needs an act whose expected
value was known and whose body was kept, which is an act that already ran. What it buys is
the SECOND run of a destination this one could not check -- which is the same shape as
`run/select.py`, and for the same reason.
"""

from __future__ import annotations

from typing import Any

from factory.core.contract import Contract
from factory.core.evidence import Did

#: How deep a path is worth following. A value found under twelve levels of envelope is
#: more likely a coincidence than a field, and a path nobody can read is not evidence.
DEEPEST = 6


def _paths(body: Any, at: tuple[str, ...] = ()) -> list[tuple[tuple[str, ...], str]]:
    """Every leaf in a parsed body, as the path to it and what it holds."""
    if len(at) > DEEPEST:
        return []
    if isinstance(body, dict):
        return [found for key, value in body.items()
                for found in _paths(value, (*at, str(key)))]
    if isinstance(body, list):
        #: The index is deliberately NOT part of the path. A record set is read row by row,
        #: and a path carrying `[3]` would only ever find the row it was learned from.
        return [found for item in body for found in _paths(item, at)]
    return [(at, str(body))] if body is not None else []


def mapping(contract: Contract, did: Did) -> dict[str, tuple[str, ...]]:
    """For each expected field, where in what the page fetched its value actually sat.

    ONE PATH PER FIELD, THE SHALLOWEST. Two paths carrying the same value is the ordinary
    case -- an id echoed in a header and in a record -- and the shallower one is the one
    that survives the envelope changing around it.

    A FIELD ALREADY READABLE IS NOT LEARNED. If the body carries the value under the name
    the contract already uses, `Fetched` would have found it and this act would not be
    here; recording it anyway would build a mapping that says nothing.
    """
    import json

    learned: dict[str, tuple[str, ...]] = {}
    for exchange in did.exchanges:
        if not exchange.body:
            continue
        try:
            parsed = json.loads(exchange.body)
        except (ValueError, TypeError):
            continue
        for path, held in _paths(parsed):
            for field, want in contract.expects.items():
                if held != want or path[-1:] == (field,):
                    continue
                if field not in learned or len(path) < len(learned[field]):
                    learned[field] = path
    return learned


def merged(known: dict[str, tuple[str, ...]],
           found: dict[str, tuple[str, ...]]) -> dict[str, tuple[str, ...]]:
    """What is known about a surface, plus what this act taught, without losing either.

    A LATER LESSON DOES NOT OVERWRITE AN EARLIER ONE ON EQUAL EVIDENCE. Same field, same
    depth: the first stands. Every entry here was equality against a value we expected, so
    churning between two of them would be noise rather than learning.
    """
    together = dict(known)
    for field, path in found.items():
        if field not in together or len(path) < len(together[field]):
            together[field] = path
    return together
