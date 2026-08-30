"""EXECUTION, then WORKFLOW, then MAIN. First hit wins, and that IS the inheritance.

Nothing is copied between tiers. A narrower entry shadows a wider one for as long as it
exists, and disappears with the thing that scoped it.
"""

from __future__ import annotations

from factory.core.memory import Tier


def chain(run: str = "", workflow: str = "") -> tuple[tuple[Tier, str], ...]:
    """The lookup order for one moment, narrowest first.

    A tier with nothing to scope it is skipped rather than searched with an empty scope,
    which would otherwise match every entry at that tier.
    """
    order: list[tuple[Tier, str]] = []
    if run:
        order.append((Tier.EXECUTION, run))
    if workflow:
        order.append((Tier.WORKFLOW, workflow))
    order.append((Tier.MAIN, ""))
    return tuple(order)


def wider(tier: Tier) -> Tier | None:
    """Where an entry goes when it has earned promotion. MAIN is the top."""
    return {Tier.EXECUTION: Tier.WORKFLOW, Tier.WORKFLOW: Tier.MAIN}.get(tier)


def narrower(tier: Tier) -> Tier | None:
    """Where an entry falls when a witness refutes it. Below EXECUTION is gone."""
    return {Tier.MAIN: Tier.WORKFLOW, Tier.WORKFLOW: Tier.EXECUTION}.get(tier)
