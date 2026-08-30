"""Break each mechanism and ask whether anything noticed.

    uv run python -m evals.mutation

A green suite is evidence about the code only if it would go red when the code is wrong.
Nothing here tests the system; it tests the suites, by breaking one mechanism at a time and
requiring that some suite fails. **A mutation nothing notices is a gate that passes with the
gate deleted**, which this tree has already shipped once and caught once by accident.

A mutation names the claim it should invalidate. If it survives, either the claim is untested
or the mechanism was never load-bearing -- and both are findings, not noise.
"""

from __future__ import annotations

import asyncio
import contextlib
import importlib
import inspect
import io
import os
import sys
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from factory.core.contract import Receipt, Verdict
from factory.kernel.venv import HERE, KEEP
from factory.witness.channel import Channel


@dataclass(frozen=True)
class Mutation:
    """One mechanism, broken on purpose."""

    name: str
    #: The claim that should stop holding. Named so a survivor says what is untested.
    invalidates: str
    module: str
    #: Dotted from the module, so a method on a class is reachable: `Bridge._config`.
    attribute: str
    replacement: object
    #: Which suites can notice this. Scoped because a suite that launches a runtime or a
    #: browser costs seconds, and running every one against every mutation buys nothing.
    suites: tuple[str, ...] = ()


def _confirms_everything(contract, reading, *, reader: str = "", channel: str = "") -> Receipt:
    """A judge with every refusal removed. The laziest possible wrong answer."""
    return Receipt(verdict=Verdict.CONFIRMED, reader=reader, channel=channel, why="mutated")


def _inherits_everything(cell_env: dict[str, str] | None = None) -> dict[str, str]:
    """A kernel environment with the allowlist removed. What inheriting os.environ means."""
    return dict(os.environ)


def _answers_for_any_server(self, data: dict[str, object]) -> dict[str, object]:
    """A bridge that declares whatever it is asked for. What losing the registry means."""
    return {"status": "ok", "result": {"type": "http", "url": "http://127.0.0.1:1/mcp"}}


def _repo_on_the_path() -> dict[str, str]:
    """The allowlist kept, but the factory made importable from inside a cell."""
    kept = {name: os.environ[name] for name in KEEP if name in os.environ}
    return kept | {"PYTHONPATH": str(HERE), "PYTHONNOUSERSITE": "1"}


MUTATIONS = (
    Mutation(
        name="a channel we authored may witness",
        invalidates="render-only and injected readers are refused",
        module="factory.witness.channel", attribute="QUALITY",
        replacement=(Channel.DESTINATION, Channel.WIRE, Channel.DOM, Channel.DISPATCH)),

    Mutation(
        name="evidence quality reversed",
        invalidates="a lower reader never overrides a higher one",
        module="factory.witness.channel", attribute="QUALITY",
        replacement=(Channel.WIRE, Channel.DESTINATION)),

    Mutation(
        name="blindness is never detected",
        invalidates="a reader that cannot read a field refuses instead of guessing",
        module="factory.witness.judge", attribute="unreadable",
        replacement=lambda contract, reading: frozenset()),

    Mutation(
        name="every reading confirms",
        invalidates="the whole ladder",
        module="factory.witness.ladder", attribute="judge",
        replacement=_confirms_everything),

    Mutation(
        name="a cell inherits our environment",
        invalidates="K1, no secret reaches a cell",
        module="factory.kernel.venv", attribute="environment",
        replacement=_inherits_everything,
        suites=("evals.kernel.kernel_eval",)),

    Mutation(
        name="the factory is on a cell's path",
        invalidates="K2, the factory is not importable from a cell",
        module="factory.kernel.venv", attribute="environment",
        replacement=_repo_on_the_path,
        suites=("evals.kernel.kernel_eval",)),

    Mutation(
        name="the host declares any server asked for",
        invalidates="W5, a cell reaches only what the host named",
        module="factory.kernel.tools", attribute="Bridge._config",
        replacement=_answers_for_any_server,
        suites=("evals.kernel.wire_eval",)),
)

#: Where a mutation is checked when it names no suite of its own.
SUITES = ("evals.witness.witness_eval", "evals.witness.mutation_eval")



def _owner(module: object, dotted: str) -> tuple[object, str]:
    """The object holding the final name, and that name. `getattr` does not walk dots."""
    *path, name = dotted.split(".")
    for step in path:
        module = getattr(module, step)
    return module, name


def noticed(suite: str) -> bool:
    """Whether this suite fails right now. Its own output is not this module's output.

    A suite's `run` may be a coroutine function -- anything driving a browser or a runtime
    is. Calling one without awaiting it returns a coroutine object, and `!= 0` on that is
    always true, so every mutation reads as caught and the harness certifies nothing.
    Measured: both kernel mutations passed this way before the check below existed.
    """
    run: Callable[[], int | Awaitable[int]] = importlib.import_module(suite).run
    with contextlib.redirect_stdout(io.StringIO()):
        answer = run()
        if inspect.isawaitable(answer):
            answer = asyncio.run(answer)
    return answer != 0


def run() -> int:
    survivors = 0
    for mutation in MUTATIONS:
        holder, name = _owner(importlib.import_module(mutation.module), mutation.attribute)
        original = getattr(holder, name)
        setattr(holder, name, mutation.replacement)
        try:
            caught = any(noticed(suite) for suite in (mutation.suites or SUITES))
        finally:
            setattr(holder, name, original)

        survivors += not caught
        print(f"{'caught  ' if caught else 'SURVIVED'} {mutation.name:38} "
              f"-> {mutation.invalidates}")

    print(f"\nSURVIVED  broken and nothing failed : {survivors}   (must be 0)")
    if not survivors:
        print("every mechanism above is load-bearing, and some suite depends on each")
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(run())
