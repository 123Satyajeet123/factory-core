
from __future__ import annotations

from collections.abc import Awaitable, Callable
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from factory.capability.amortize import Reviewed, Worth, retired, reviewed
from factory.capability.discriminate import discriminates, ignored
from factory.capability.draft import NotDrafted, draft
from factory.capability.offer import offer
from factory.capability.prove import Proven, prove
from factory.capability.publish import write
from factory.capability.worth import judge
from factory.core.contract import Contract
from factory.core.evidence import Run
from factory.core.workflow import Workflow
from factory.kernel.skills import NotInstallable


class Observed(BaseModel):

    sent: Any = None
    returned: Any = None


Watch = Callable[[str], Awaitable[Observed]]


class Standing(StrEnum):
    ADMITTED = "admitted"
    HELD = "held"
    REFUSED = "refused"


class Considered(BaseModel):

    name: str
    standing: Standing
    passed: tuple[str, ...] = ()
    gate: str = ""
    why: str = ""

    def __bool__(self) -> bool:
        return self.standing is Standing.ADMITTED

    def line(self) -> str:
        got = f" at {self.gate}" if self.gate else ""
        return f"{self.standing:8} {self.name}{got}: {self.why}"


class Capabilities:

    def __init__(self, kernel: Any, into: Path) -> None:
        self.kernel = kernel
        self.into = into

    async def consider(self, workflow: Workflow, run: Run, *, name: str | None = None,
                       watch: Watch | None = None, witness: Any = None,
                       contract: Contract | None = None,
                       installed: dict[str, tuple[str, ...]] | None = None,
                       inputs: tuple[str, str] = ("'one'", "'two'")) -> Considered:
        passed: list[str] = []

        merit = judge(workflow, installed or {})
        if not merit:
            return Considered(name=name or workflow.name, standing=Standing.REFUSED,
                              gate="worth", why=merit.why())
        passed.append("worth")

        try:
            candidate = draft(workflow, run, name=name)
        except NotDrafted as why:
            return Considered(name=name or workflow.name, standing=Standing.REFUSED,
                              gate="draft", why=str(why))
        passed.append("draft")

        blind = ignored(candidate)
        if blind:
            return Considered(name=candidate.name, standing=Standing.REFUSED, passed=tuple(passed),
                              gate="discriminate", why=f"ignores {', '.join(sorted(blind))}")
        passed.append("discriminate:reading")

        root = write(self.into, candidate)
        passed.append("publish")

        try:
            await offer(self.kernel, root, inputs[0])
        except NotInstallable as why:
            return Considered(name=candidate.name, standing=Standing.REFUSED, passed=tuple(passed),
                              gate="offer", why=str(why))
        passed.append("offer")

        if watch is None:
            return Considered(
                name=candidate.name, standing=Standing.HELD, passed=tuple(passed),
                gate="discriminate:behaviour",
                why="nothing observed what it sent, so its arguments cannot be shown to matter")

        first, second = await watch(inputs[0]), await watch(inputs[1])
        answer = discriminates(candidate, (first.sent, second.sent))
        if not answer:
            return Considered(name=candidate.name, standing=Standing.REFUSED, passed=tuple(passed),
                              gate="discriminate:behaviour", why=answer.why())
        passed.append("discriminate:behaviour")

        if contract is None:
            return Considered(name=candidate.name, standing=Standing.HELD, passed=tuple(passed),
                              gate="prove", why="nothing said what this step should make true")
        shown = prove(candidate.name, second.returned, contract, witness)
        if shown.standing is not Proven.PROVEN:
            standing = Standing.REFUSED if shown.standing in (
                Proven.REFUTED, Proven.BROKEN) else Standing.HELD
            return Considered(name=candidate.name, standing=standing, passed=tuple(passed),
                              gate="prove", why=shown.line())
        passed.append("prove")

        return Considered(name=candidate.name, standing=Standing.ADMITTED,
                          passed=tuple(passed), why=f"{len(passed)} gates")

    def reexamine(self, every: list[Worth]) -> list[Reviewed]:
        return reviewed(every)

    def no_longer_offered(self, every: list[Worth]) -> list[str]:
        return retired(self.reexamine(every))
