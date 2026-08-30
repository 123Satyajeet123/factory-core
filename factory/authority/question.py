
from __future__ import annotations

import sqlite3

from factory.core.drivers import Asks
from factory.core.question import Question
from factory.store import questions


class Authority:

    def __init__(self, db: sqlite3.Connection, asks: Asks | None = None) -> None:
        self.db = db
        self.asks = asks

    def ask(self, question: Question) -> str | None:
        known = questions.recall(self.db, question)
        if known is not None:
            return known

        questions.record(self.db, question)
        if self.asks is None:
            return None

        given = self.asks(question)
        if not given:
            return None
        questions.answer(self.db, question, given)
        return given

    def waiting(self) -> list[Question]:
        return questions.waiting(self.db)
