
from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime

from factory.core.question import Ask, Question


def _now() -> str:
    return datetime.now(UTC).isoformat()


def record(db: sqlite3.Connection, question: Question) -> None:
    db.execute(
        "INSERT INTO question (kind, about, because, candidates, asked_at) "
        "VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT (kind, about) DO UPDATE SET because = excluded.because, "
        "candidates = excluded.candidates, asked_at = excluded.asked_at",
        (question.kind, question.about, question.because,
         json.dumps(list(question.candidates)), _now()))


def answer(db: sqlite3.Connection, question: Question, given: str) -> None:
    record(db, question)
    db.execute("UPDATE question SET answer = ?, answered_at = ? WHERE kind = ? AND about = ?",
               (given, _now(), question.kind, question.about))


def recall(db: sqlite3.Connection, question: Question) -> str | None:
    row = db.execute("SELECT answer FROM question WHERE kind = ? AND about = ?",
                     (question.kind, question.about)).fetchone()
    return row["answer"] or None if row else None


def waiting(db: sqlite3.Connection) -> list[Question]:
    return [
        Question(kind=Ask(row["kind"]), about=row["about"], because=row["because"],
                 candidates=tuple(json.loads(row["candidates"] or "[]")))
        for row in db.execute(
            "SELECT * FROM question WHERE answer IS NULL OR answer = '' ORDER BY asked_at")
    ]
