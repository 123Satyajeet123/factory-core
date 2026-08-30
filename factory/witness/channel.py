"""A channel that did not perform the act, and the order they rank in.

The defining property of this driver: an act and its confirmation cannot share an author.
If we produced the bytes, reading them back reports what we did and never what happened.

DOM IS OURS, and it is the non-obvious member. A click mutates the document directly, and
nothing in the document separates a mutation we caused from one a server caused. A channel
we cannot prove we did not author cannot witness -- conservative is the only safe direction
when FALSE CONFIRMED must be 0.

ONE LIST, TWO JOBS, AND THAT IS DELIBERATE. Membership in `QUALITY` decides whether a
channel may witness at all; position decides which rung is asked first. A separate set of
"channels that are ours" would be a second mechanism doing the same job, and the two would
drift the first time a channel is added.
"""

from __future__ import annotations

from enum import StrEnum


class Channel(StrEnum):
    """Where bytes came from, which is what decides whether they can witness."""

    DISPATCH = "dispatch"
    DOM = "dom"
    WIRE = "wire"
    DESTINATION = "destination"


#: Ordered by evidence quality, best first. Fixed, and not scored on outcomes:
#: `run/select.py` is ordered by cost and IS learned, which is a different question. A
#: channel absent here -- DISPATCH, DOM -- carries bytes we authored.
QUALITY: tuple[Channel, ...] = (Channel.DESTINATION, Channel.WIRE)


def can_witness(channel: Channel) -> bool:
    """Whether a channel may witness an act at all."""
    return channel in QUALITY


def evidence_rank(channel: Channel) -> int:
    """Rank, best first. Only meaningful for a channel that witnesses."""
    return QUALITY.index(channel)
