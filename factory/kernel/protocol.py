
from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

PROTOCOL = 3


class Status(StrEnum):

    OK = "ok"
    ERROR = "error"


class Cell(BaseModel):

    id: str
    status: Status
    result: str | None = None
    out: list[str] = Field(default_factory=list)
    err: list[str] = Field(default_factory=list)
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
    return {"type": "interrupt"} | ({"id": cell_id} if cell_id else {})


def shutdown() -> dict[str, str]:
    return {"type": "shutdown"}
