"""Ordered by evidence quality, and therefore fixed.

Not scored on outcomes and not learned. `run/select.py` is ordered by cost and IS learned;
conflating the two would let a cheap channel outrank a truthful one, which is the one trade
this driver may never make.

A LOWER RUNG NEVER OVERRIDES A HIGHER ONE. The first rung that is not blind decides,
including when it refutes. Walking on after a refutation to look for a confirmation is how a
system talks itself into an answer.
"""

from __future__ import annotations

from collections.abc import Iterable

from factory.core.contract import Contract, Receipt, Verdict
from factory.core.evidence import Did
from factory.witness.channel import can_witness, evidence_rank
from factory.witness.judge import judge
from factory.witness.readers import Reader, discover


class Ladder:
    """The admissible readers, best evidence first."""

    def __init__(self, readers: Iterable[Reader] | None = None) -> None:
        self.readers = tuple(readers) if readers is not None else discover()

    def admissible(self) -> tuple[Reader, ...]:
        """Readers that may witness, in quality order. Ours are refused, not ranked low."""
        return tuple(sorted(
            (reader for reader in self.readers if can_witness(reader.channel)),
            key=lambda reader: evidence_rank(reader.channel)))

    def inadmissible(self) -> tuple[Reader, ...]:
        """Readers on channels we authored. Counted, so a silent refusal is not silent."""
        return tuple(r for r in self.readers if not can_witness(r.channel))

    def witness(self, did: Did, contract: Contract) -> Receipt:
        """The first rung that can see the expected fields decides.

        With no admissible reader the answer is UNVERIFIABLE and never CONFIRMED: nothing
        was checked, which is not the same as nothing being wrong.
        """
        answer = Receipt(verdict=Verdict.UNVERIFIABLE, why="no admissible reader")
        for reader in self.admissible():
            answer = judge(contract, reader.read(did, contract),
                           reader=reader.name, channel=reader.channel)
            if answer.verdict is not Verdict.UNVERIFIABLE:
                return answer
        return answer
