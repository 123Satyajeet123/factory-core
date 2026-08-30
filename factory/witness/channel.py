
from __future__ import annotations

from enum import StrEnum


class Channel(StrEnum):

    DISPATCH = "dispatch"
    DOM = "dom"
    WIRE = "wire"
    DESTINATION = "destination"


QUALITY: tuple[Channel, ...] = (Channel.DESTINATION, Channel.WIRE)


def can_witness(channel: Channel) -> bool:
    return channel in QUALITY


def evidence_rank(channel: Channel) -> int:
    return QUALITY.index(channel)
