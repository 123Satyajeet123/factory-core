
from __future__ import annotations

from datetime import datetime, timedelta
from itertools import pairwise

from pydantic import BaseModel

from factory.core.ledger import Segment
from factory.store import ledger

SITTING = timedelta(hours=6)

ENOUGH = 2


class Noticed(BaseModel):

    task: str
    demonstrations: int = 0
    sittings: int = 0
    undated: int = 0

    def __bool__(self) -> bool:
        return self.sittings >= ENOUGH

    def why(self) -> str:
        if self.undated and not self.sittings:
            return f"{self.undated} demonstrations carry no time"
        if self:
            return f"{self.demonstrations} demonstrations across {self.sittings} sittings"
        return f"{self.demonstrations} demonstrations, all within one sitting"


def when(segment: Segment) -> datetime | None:
    return segment.acts[0].at if segment.acts else None


def sittings(segments: list[Segment], gap: timedelta = SITTING) -> int:
    times = sorted(at for at in map(when, segments) if at is not None)
    if not times:
        return 0
    return 1 + sum(later - earlier >= gap for earlier, later in pairwise(times))


def across(task: str, segments: list[Segment], gap: timedelta = SITTING) -> Noticed:
    shown = [s for s in segments if s.by_person()]
    return Noticed(task=task, demonstrations=len(shown),
                   sittings=sittings(shown, gap),
                   undated=sum(when(s) is None for s in shown))


def worth_compiling(gap: timedelta = SITTING, at=ledger.HOME) -> list[Noticed]:
    seen = (across(task, ledger.shown(task, at), gap) for task in ledger.tasks(at))
    return sorted((n for n in seen if n), key=lambda n: -n.sittings)
