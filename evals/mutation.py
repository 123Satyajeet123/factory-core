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

import contextlib
import importlib
import io
import sys
from collections.abc import Callable
from dataclasses import dataclass

from factory.core.contract import Receipt, Verdict
from factory.witness.channel import Channel


@dataclass(frozen=True)
class Mutation:
    """One mechanism, broken on purpose."""

    name: str
    #: The claim that should stop holding. Named so a survivor says what is untested.
    invalidates: str
    module: str
    attribute: str
    replacement: object


def _confirms_everything(contract, reading, *, reader: str = "", channel: str = "") -> Receipt:
    """A judge with every refusal removed. The laziest possible wrong answer."""
    return Receipt(verdict=Verdict.CONFIRMED, reader=reader, channel=channel, why="mutated")


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
)

#: The suites a mutation is allowed to be caught by. Any one failing is enough.
SUITES = ("evals.witness.witness_eval",)


def noticed(suite: str) -> bool:
    """Whether this suite fails right now. Its own output is not this module's output."""
    run: Callable[[], int] = importlib.import_module(suite).run
    with contextlib.redirect_stdout(io.StringIO()):
        return run() != 0


def run() -> int:
    survivors = 0
    for mutation in MUTATIONS:
        module = importlib.import_module(mutation.module)
        original = getattr(module, mutation.attribute)
        setattr(module, mutation.attribute, mutation.replacement)
        try:
            caught = any(noticed(suite) for suite in SUITES)
        finally:
            setattr(module, mutation.attribute, original)

        survivors += not caught
        print(f"{'caught  ' if caught else 'SURVIVED'} {mutation.name:38} "
              f"-> {mutation.invalidates}")

    print(f"\nSURVIVED  broken and nothing failed : {survivors}   (must be 0)")
    if not survivors:
        print("every mechanism above is load-bearing, and some suite depends on each")
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(run())
