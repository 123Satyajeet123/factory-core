"""What a run did, kept, so the claim that it gets cheaper can be checked.

WITHOUT THIS THE HEADLINE NUMBER IS UNFALSIFIABLE. `observe.cheaper` compares two runs, and
the comparison is the claim this system rests on -- an absolute cost is what a run was worth
to somebody selling capacity; whether run forty needed less help than run one is the only
number that says the factory did what it says. A run that dies with its process cannot be
one end of that comparison.

RECEIPTS TRAVEL WITH IT. A `Run` carries its rows, its steps, its verdicts and which rung
answered each one, so nothing has to be stored twice and no summary can disagree with what
it summarises. `observe.spent` derives the cost from the run rather than from a number
written beside it.

NOT WHAT MEMORY IS FOR. `store/db.py` holds what a later run LOOKS UP -- a resolution, a
permit, an answer -- and those already survive. This holds what a later run is COMPARED to.
"""

from __future__ import annotations

from pathlib import Path

from factory.core.evidence import Run
from factory.store import kept

HOME = kept.HOME / "runs"


def keep(run: Run, task: str, at: Path = HOME) -> Path:
    """Write one run. Numbered, never overwritten."""
    return kept.keep(run, task, at)


def of(task: str, at: Path = HOME) -> list[Run]:
    """Every run of one task, oldest first."""
    return kept.read(Run, task, at)


def tasks(at: Path = HOME) -> list[str]:
    return kept.tasks(at)
