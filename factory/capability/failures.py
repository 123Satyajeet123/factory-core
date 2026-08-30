
from __future__ import annotations

from pydantic import BaseModel

from factory.capability.variations import Attempt


class Guard(BaseModel):

    step: int
    because: str
    failures: int = 0
    inputs: tuple[str, ...] = ()

    def line(self) -> str:
        which = ", ".join(self.inputs[:3]) + ("..." if len(self.inputs) > 3 else "")
        return f"before step {self.step}: {self.because}  ({self.failures}x: {which})"


def guards(attempts: list[Attempt], *, least: int = 2) -> tuple[Guard, ...]:
    failed = [a for a in attempts if not a.held and a.stopped_at is not None]
    held = [a for a in attempts if a.held]
    if not failed:
        return ()
    if not held:
        return ()

    reached = max((len(a.acts) for a in held), default=0)

    seen: dict[tuple[int, str], list[str]] = {}
    for attempt in failed:
        seen.setdefault((attempt.stopped_at, attempt.why), []).append(attempt.arguments)

    found = []
    for (step, why), inputs in sorted(seen.items()):
        if len(inputs) < least:
            continue
        if held and reached <= step:
            continue
        found.append(Guard(step=step, because=why, failures=len(inputs),
                           inputs=tuple(inputs)))
    return tuple(found)


def always_fails(attempts: list[Attempt]) -> bool:
    return bool(attempts) and not any(a.held for a in attempts)
