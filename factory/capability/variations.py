
from __future__ import annotations

import ast
from typing import Any

from pydantic import BaseModel

from factory.core.evidence import Did


class Attempt(BaseModel):

    arguments: str
    acts: list[Did] = []
    stopped_at: int | None = None
    why: str = ""

    @property
    def held(self) -> bool:
        return self.stopped_at is None and bool(self.acts)

    def line(self) -> str:
        where = "held" if self.held else f"stopped at step {self.stopped_at}"
        return f"{self.arguments:24} {len(self.acts)} acts, {where}: {self.why or 'ok'}"


def read(arguments: str, answered: Any) -> Attempt:
    if not isinstance(answered, list):
        return Attempt(arguments=arguments, why="it answered nothing")
    acts = [Did.model_validate(one) for one in answered if isinstance(one, dict)]
    for index, act in enumerate(acts):
        if not act.ok:
            return Attempt(arguments=arguments, acts=acts, stopped_at=index,
                           why=act.detail or str(act.delivery))
    return Attempt(arguments=arguments, acts=acts)


async def across(kernel: Any, module: str, inputs: list[str], *,
                 timeout: float = 120.0) -> list[Attempt]:
    attempts = []
    for arguments in inputs:
        cell = await kernel.run(f"await {module}.run({arguments})", timeout=timeout)
        if cell.status != "ok":
            attempts.append(Attempt(arguments=arguments, why=f"{cell.ename}: {cell.evalue}"))
            continue
        attempts.append(read(arguments, ast.literal_eval(cell.result) if cell.result else None))
    return attempts
