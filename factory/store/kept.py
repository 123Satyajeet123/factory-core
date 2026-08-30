"""Evidence on disk: numbered JSON files, grouped by the task they belong to.

ONE MECHANISM, TWO KINDS OF EVIDENCE. Demonstrations and runs are both append-only records
of something that happened, keyed by task, that must be readable without this program. Two
stores would be the same forty lines twice, and they would drift the first time one learned
to prune, to compress, or to name a file differently.

NUMBERED, NEVER OVERWRITTEN. What happened is not editable. A record that can be replaced
is a record that can be quietly corrected, and the whole value of evidence is that nobody
can.

PLAIN JSON, NOT A DATABASE. `store/db.py` holds what is looked up by key -- entries,
questions, permits. This holds what is read whole and rarely: a run, a demonstration. A
file somebody can open in an editor at three in the morning is worth more here than an
index nobody queries.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

HOME = Path.home() / ".factory"


def slug(task: str) -> str:
    """A task name as a directory name. Two tasks that differ only in case are one task."""
    return "".join(c if c.isalnum() else "-" for c in task.strip().lower()).strip("-")


def keep(record: BaseModel, task: str, at: Path) -> Path:
    """Write one record. Numbered by how many are already there."""
    folder = at / slug(task)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{len(list(folder.glob('*.json'))):03d}.json"
    path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
    return path


def read[Record: BaseModel](kind: type[Record], task: str, at: Path) -> list[Record]:
    """Every record of one task, oldest first. The order is the numbering."""
    folder = at / slug(task)
    if not folder.exists():
        return []
    return [kind.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(folder.glob("*.json"))]


def tasks(at: Path) -> list[str]:
    return sorted(p.name for p in at.iterdir() if p.is_dir()) if at.exists() else []


def _self_check() -> None:
    """Numbering, round trip, and one task not reading another's records.

        uv run python -m factory.store.kept
    """
    import tempfile

    from factory.core.evidence import RowRun, Run

    with tempfile.TemporaryDirectory() as home:
        at = Path(home)
        first = keep(Run(workflow="outreach", rows=[RowRun(row={"n": "1"})]), "outreach", at)
        second = keep(Run(workflow="outreach", rows=[RowRun(row={"n": "2"})]), "outreach", at)
        keep(Run(workflow="other"), "Something Else", at)

        assert first.name == "000.json" and second.name == "001.json", (first, second)
        assert first.read_text(encoding="utf-8") != second.read_text(encoding="utf-8")

        back = read(Run, "outreach", at)
        assert [row.row["n"] for run in back for row in run.rows] == ["1", "2"], back
        assert len(read(Run, "Something Else", at)) == 1, "one task does not read another's"
        assert read(Run, "never happened", at) == [], "a task with no records reads empty"

        #: A name that is not a directory name must still round trip to the same folder.
        assert slug("Something Else") == slug("something-else") == "something-else"
        assert sorted(tasks(at)) == ["outreach", "something-else"], tasks(at)
    print("kept: numbered, ordered, round tripped, and one task per folder")


if __name__ == "__main__":
    _self_check()
