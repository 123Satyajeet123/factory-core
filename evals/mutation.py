"""Break each mechanism and ask whether anything noticed.

    uv run python -m evals.mutation

A green suite is evidence about the code only if it would go red when the code is wrong.
Nothing here tests the system; it tests the suites, by breaking one mechanism at a time and
requiring that some suite fails. **A mutation nothing notices is a gate that passes with the
gate deleted**, which this tree has already shipped once and caught once by accident.

A mutation names the claim it should invalidate. If it survives, either the claim is untested
or the mechanism was never load-bearing -- and both are findings, not noise.

WHY NOT mutmut OR cosmic-ray, named so the drop is visible. Both mutate the AST -- flipping
operators, altering constants -- generate thousands of mutants and report which survive a
test suite. That answers "is this line covered". This answers "is this CLAIM checked": each
mutation below is semantic, hand-chosen, and carries the sentence it should falsify, so a
survivor names the untested claim rather than a line number. They are complements, not
alternatives, and the reason ours exists is that a survivor here is readable. Adopting one
of them later to find mutations nobody thought of would not replace this file.
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
from typing import Any

from factory.browser.bodies import worth_reading
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


async def _keeps_everything(self, cdp: Any) -> list[Any]:
    """A collector that accumulates. What `drain` returning every response ever means."""
    from factory.core.evidence import Exchange

    taken, self._pending = self._pending, {}
    for request_id, seen in taken.items():
        body = None
        if worth_reading(seen["content_type"]):
            with contextlib.suppress(Exception):
                body = (await cdp.send("Network.getResponseBody",
                                       {"requestId": request_id})).get("body")
        self._ever = getattr(self, "_ever", [])
        self._ever.append(Exchange(url=seen["url"], status=seen["status"],
                                   content_type=seen["content_type"],
                                   size=len(body or ""), body=body))
    return getattr(self, "_ever", [])


def _learns_from_resemblance(contract, did) -> dict[str, tuple[str, ...]]:
    """A mapping built from a value that merely LOOKS like the one expected.

    The one way a learned reader manufactures a false confirmation rather than missing one:
    bind a path because something near it resembled the expectation, and every later run
    confirms against whatever sits there.
    """
    import json

    from factory.witness.learn import _paths

    learned: dict[str, tuple[str, ...]] = {}
    for exchange in did.exchanges:
        if not exchange.body:
            continue
        try:
            parsed = json.loads(exchange.body)
        except (ValueError, TypeError):
            continue
        for path, held in _paths(parsed):
            for field, want in contract.expects.items():
                if field not in learned and (held in want or want in held or held):
                    learned[field] = path
    return learned


def _never_stops_being_true(self, now: Any = None) -> bool:
    """An entry whose validity cannot end. What counting receipts without ordering means."""
    return True


MUTATIONS = (
    Mutation(
        name="an entry's validity never ends",
        invalidates="a long record that broke is not answered with until it works again",
        module="factory.core.memory", attribute="Entry.standing",
        replacement=_never_stops_being_true,
        suites=("factory.memory.driver",)),

    Mutation(
        name="a path is learned from resemblance, not equality",
        invalidates="nothing is learned from a body that never carried the value",
        module="factory.witness.learn", attribute="mapping",
        replacement=_learns_from_resemblance,
        suites=("evals.witness.learned_eval",)),

    Mutation(
        name="evidence outlives the act it belongs to",
        invalidates="an act is never confirmed by another act's evidence",
        module="factory.browser.bodies", attribute="Bodies.drain",
        replacement=_keeps_everything,
        suites=("evals.witness.stale_eval",)),

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
    module = importlib.import_module(suite)
    #: THREE ENTRY SHAPES EXIST IN THIS TREE and this file used to assume one. `any()`
    #: short-circuits, so the second suite in `SUITES` was only ever reached when the first
    #: failed to catch -- exactly the case a survivor is reported from -- and it raised
    #: AttributeError there instead. A latent crash in the guard of the guards.
    run: Callable[[], int | Awaitable[int]] | None = next(
        (found for found in (getattr(module, name, None)
                             for name in ("run", "main", "_self_check")) if found), None)
    if run is None:
        raise AttributeError(f"{suite} offers no run(), main() or _self_check()")
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            answer = run()
            if inspect.isawaitable(answer):
                answer = asyncio.run(answer)
        except AssertionError:
            #: A `_self_check` reports by raising. Noticing is noticing.
            return True
    return bool(answer)


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
