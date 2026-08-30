"""The wire, as types. Protocol 3, from `rlm/repl.md` at the pinned revision.

Newline-delimited JSON, one object per line, UTF-8, no other framing. Requests go to the
child's stdin; events arrive on its stdout, which the runtime dups from the original fd 1
before anything else runs -- so user output cannot corrupt framing and every line read here
is a protocol frame.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

#: The runtime announces this in its `ready` event. A different number means the frames
#: below may not describe what is on the wire, so the handshake refuses rather than adapts.
PROTOCOL = 3


class Status(StrEnum):
    """How a request ended. Every id'd request emits exactly one `done`."""

    OK = "ok"
    ERROR = "error"


class Cell(BaseModel):
    """One execution and everything the runtime said about it.

    `result` is the repr of a trailing expression, present only when the cell body ends in
    one whose value is not None. Output arrives on two channels -- Python-level writes
    tagged with the cell id, and raw fd bytes that carry `id: null` -- and ordering is
    preserved within each channel but not across them, so they are kept apart.
    """

    id: str
    status: Status
    result: str | None = None
    out: list[str] = Field(default_factory=list)
    err: list[str] = Field(default_factory=list)
    #: Present when status is ERROR. `ename` is KeyboardInterrupt for an interrupted cell.
    ename: str = ""
    evalue: str = ""
    traceback: list[str] = Field(default_factory=list)
    seconds: float = 0.0

    @property
    def interrupted(self) -> bool:
        return self.ename == "KeyboardInterrupt"


def execute(cell_id: str, code: str) -> dict[str, str]:
    return {"type": "execute", "id": cell_id, "code": code}


def interrupt(cell_id: str | None = None) -> dict[str, str]:
    """No reply. Parked if the request has not started; dropped if it has finished."""
    return {"type": "interrupt"} | ({"id": cell_id} if cell_id else {})


def shutdown() -> dict[str, str]:
    """Closing stdin is equivalent. Kills live bash child groups, then exits 0."""
    return {"type": "shutdown"}
