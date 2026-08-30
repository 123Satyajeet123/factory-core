
from __future__ import annotations

from collections.abc import Iterable

from factory.core.contract import Contract, Receipt, Verdict
from factory.core.evidence import Did
from factory.witness.channel import can_witness, evidence_rank
from factory.witness.judge import judge
from factory.witness.readers import Reader, discover


class Ladder:

    def __init__(self, readers: Iterable[Reader] | None = None) -> None:
        self.readers = tuple(readers) if readers is not None else discover()

    def admissible(self) -> tuple[Reader, ...]:
        return tuple(sorted(
            (reader for reader in self.readers if can_witness(reader.channel)),
            key=lambda reader: evidence_rank(reader.channel)))

    def inadmissible(self) -> tuple[Reader, ...]:
        return tuple(r for r in self.readers if not can_witness(r.channel))

    def witness(self, did: Did, contract: Contract) -> Receipt:
        answer = Receipt(verdict=Verdict.UNVERIFIABLE, why="no admissible reader")
        for reader in self.admissible():
            answer = judge(contract, reader.read(did, contract),
                           reader=reader.name, channel=reader.channel)
            if answer.verdict is not Verdict.UNVERIFIABLE:
                return answer
        return answer
