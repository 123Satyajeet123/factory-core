
from __future__ import annotations

import ast

from pydantic import BaseModel

from factory.capability.publish import Capability


class Discrimination(BaseModel):

    ignored: frozenset[str] = frozenset()
    varied: bool | None = None

    def __bool__(self) -> bool:
        return not self.ignored and self.varied is True

    def why(self) -> str:
        if self.ignored:
            return f"ignores {', '.join(sorted(self.ignored))}"
        if self.varied is None:
            return "never run, so nothing is known about what it sends"
        return "the same acts whatever it is given" if not self.varied else "arguments matter"


def ignored(capability: Capability) -> frozenset[str]:
    tree = ast.parse(capability.body)
    run = next((n for n in ast.walk(tree)
                if isinstance(n, ast.AsyncFunctionDef | ast.FunctionDef) and n.name == "run"),
               None)
    if run is None:
        return frozenset()
    declared = {arg.arg for arg in run.args.args}
    used = {n.id for n in ast.walk(run) if isinstance(n, ast.Name) and
            isinstance(n.ctx, ast.Load)}
    return frozenset(declared - used)


def varied(one: object, other: object) -> bool:
    return one != other


def discriminates(capability: Capability, sent: tuple[object, object] | None = None
                  ) -> Discrimination:
    return Discrimination(
        ignored=ignored(capability),
        varied=None if sent is None else varied(*sent))
