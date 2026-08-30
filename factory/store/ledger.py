"""Demonstrations on disk, one file each.

A ledger is the only thing in this system that cannot be regenerated: a run can be repeated
and a contract re-derived, but nobody demonstrates the same afternoon twice. So it is
written plainly -- one JSON file per segment, readable without this program.
"""

from __future__ import annotations

from pathlib import Path

from factory.core.ledger import Segment

HOME = Path.home() / ".factory" / "ledger"


def keep(segment: Segment, task: str, at: Path = HOME) -> Path:
    """Write one demonstration. Numbered, never overwritten."""
    folder = at / _slug(task)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{len(list(folder.glob('*.json'))):03d}.json"
    path.write_text(segment.model_dump_json(indent=2), encoding="utf-8")
    return path


def shown(task: str, at: Path = HOME) -> list[Segment]:
    """Every demonstration of one task, in the order they were given."""
    folder = at / _slug(task)
    return [Segment.model_validate_json(p.read_text(encoding="utf-8"))
            for p in sorted(folder.glob("*.json"))] if folder.exists() else []


def tasks(at: Path = HOME) -> list[str]:
    return sorted(p.name for p in at.iterdir() if p.is_dir()) if at.exists() else []


def _slug(task: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in task.strip().lower()).strip("-")
