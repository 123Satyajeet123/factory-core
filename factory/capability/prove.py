
from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel

from factory.core.contract import Contract, Receipt, Verdict
from factory.core.evidence import Did


class Proven(StrEnum):
    PROVEN = "proven"
    REFUTED = "refuted"
    UNPROVEN = "unproven"
    BROKEN = "broken"


class Proof(BaseModel):

    name: str
    standing: Proven
    acts: int = 0
    reader: str = ""
    why: str = ""

    def __bool__(self) -> bool:
        return self.standing is Proven.PROVEN

    def line(self) -> str:
        by = f" by {self.reader}" if self.reader else ""
        return f"{self.standing:8} {self.name}: {self.acts} acts{by}, {self.why}"


def acted(returned: object) -> list[Did]:
    if not isinstance(returned, list):
        return []
    return [Did.model_validate(one) for one in returned if isinstance(one, dict)]


def prove(name: str, returned: object, contract: Contract, ladder: Any) -> Proof:
    did = acted(returned)
    if not did:
        return Proof(name=name, standing=Proven.BROKEN, why="it reported no acts at all")
    if not all(one.ok for one in did):
        stopped = next(one for one in did if not one.ok)
        return Proof(name=name, standing=Proven.BROKEN, acts=len(did),
                     why=f"stopped: {stopped.detail}")

    if ladder is None:
        return Proof(name=name, standing=Proven.UNPROVEN, acts=len(did),
                     why="no witness, so nothing checked what the acts did")

    receipt: Receipt = ladder.witness(did[-1], contract)
    if receipt.verdict is Verdict.CONFIRMED:
        return Proof(name=name, standing=Proven.PROVEN, acts=len(did),
                     reader=receipt.reader, why=receipt.why)
    if receipt.verdict is Verdict.REFUTED:
        return Proof(name=name, standing=Proven.REFUTED, acts=len(did),
                     reader=receipt.reader, why=receipt.why)
    return Proof(name=name, standing=Proven.UNPROVEN, acts=len(did),
                 reader=receipt.reader, why=receipt.why)
