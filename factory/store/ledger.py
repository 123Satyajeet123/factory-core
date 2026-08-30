"""Demonstrations on disk, one file each.

A ledger is the only thing in this system that cannot be regenerated: a run can be repeated
and a contract re-derived, but nobody demonstrates the same afternoon twice.

THE WRITING IS `store/kept.py`. What is here is which type and which folder, because that
is all that differs between keeping a demonstration and keeping a run.
"""

from __future__ import annotations

from pathlib import Path

from factory.core.ledger import Segment
from factory.store import kept

HOME = kept.HOME / "ledger"


def keep(segment: Segment, task: str, at: Path = HOME) -> Path:
    """Write one demonstration. Numbered, never overwritten."""
    return kept.keep(segment, task, at)


def shown(task: str, at: Path = HOME) -> list[Segment]:
    """Every demonstration of one task, in the order they were given."""
    return kept.read(Segment, task, at)


def tasks(at: Path = HOME) -> list[str]:
    return kept.tasks(at)
