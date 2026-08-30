"""Does a question reach somewhere, and is a person asked the same thing twice?

    uv run python -m evals.authority.question_eval

No browser and no site. An in-memory store and a person who counts how often they were
asked, because "asked once" is the property and a count is the only way to check it.

    NAGGED    a settled question was asked again    must be 0
    LOST      a question reached nowhere            must be 0
"""

from __future__ import annotations

import sys

from factory.authority.question import Authority
from factory.core.question import Ask, Question
from factory.core.workflow import Workflow
from factory.store.db import open_at

AMBIGUOUS = Question(kind=Ask.TARGET, about="button 'Save'",
                     because="2 matches", candidates=("button 'Save'", "button 'Save as'"))
OTHER = Question(kind=Ask.TARGET, about="textbox 'Note'", because="no match")


def run() -> int:
    nagged = lost = failed = 0
    asked: list[str] = []

    def person(question: Question) -> str | None:
        """Answers the first, declines the second. Records every time it was bothered."""
        asked.append(question.about)
        return "1" if question.about == AMBIGUOUS.about else None

    def check(name: str, ok: bool, detail: str) -> None:
        nonlocal failed
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name:46} {detail}")

    db = open_at(":memory:")
    authority = Authority(db, person)

    # A1 -- an unsettled question reaches the person.
    first = authority.ask(AMBIGUOUS)
    check("A1 an unknown question is asked", first == "1" and asked == [AMBIGUOUS.about],
          f"answered {first!r}, person bothered {len(asked)}x")

    # A2 -- and never again, however many runs ask it.
    for _ in range(5):
        again = authority.ask(AMBIGUOUS)
    nagged += len(asked) - 1
    check("A2 a settled question is never re-asked", len(asked) == 1 and again == "1",
          f"6 asks, person bothered {len(asked)}x, still {again!r}")

    # A3 -- the answer survives a new Authority, which is what "outlives the run" means.
    check("A3 the answer outlives the run", Authority(db, person).ask(AMBIGUOUS) == "1",
          f"a fresh Authority on the same store, person bothered {len(asked)}x")

    # A4 -- nobody answering is not an error, and the question stays visible.
    declined = authority.ask(OTHER)
    open_now = [q.about for q in authority.waiting()]
    lost += OTHER.about not in open_now
    check("A4 an unanswered question is not lost", declined is None and OTHER.about in open_now,
          f"waiting: {open_now}")
    check("A4 and the settled one is not waiting", AMBIGUOUS.about not in open_now,
          f"{len(open_now)} waiting")

    # A5 -- with nobody to ask, it records rather than raises or guesses.
    alone = Authority(open_at(":memory:"))
    quiet = alone.ask(OTHER)
    check("A5 no one to ask is a state, not an error",
          quiet is None and [q.about for q in alone.waiting()] == [OTHER.about],
          f"returned {quiet!r}, waiting {len(alone.waiting())}")

    # A6 -- what was seen last is refreshed; the answer is not disturbed by re-asking.
    authority.ask(AMBIGUOUS.model_copy(update={"because": "3 matches now"}))
    seen = db.execute("SELECT because, answer FROM question WHERE about = ?",
                      (AMBIGUOUS.about,)).fetchone()
    check("A6 what was seen updates, the answer does not",
          seen["because"] == "2 matches" and seen["answer"] == "1",
          f"because={seen['because']!r} answer={seen['answer']!r}")

    # A7 -- the second kind reaches a destination. A workflow wants `note`; the row has
    # no such column. The answer is which column supplies it, and the row is then read
    # through it -- per-destination knowledge as data, not as code.
    from factory.run.harness import supplied

    workflow = Workflow(name="file-a-note", params=("note",))
    sheet = {"customer": "ada", "body": "hello"}

    reading, refused = supplied(workflow, sheet, None)
    lost += refused is None
    check("A7 a missing parameter is a question", refused is not None and refused.kind is Ask.PARAM,
          f"{refused.kind if refused else 'NONE'}: {refused.because if refused else ''}")
    check("A7 and it offers what the row does have",
          refused is not None and refused.candidates == ("body", "customer"),
          f"candidates {refused.candidates if refused else ()}")

    mapped: list[str] = []

    def maps_columns(question: Question) -> str:
        mapped.append(question.about)
        return "body"

    columns = Authority(open_at(":memory:"), maps_columns)
    reading, refused = supplied(workflow, sheet, columns)
    check("A7 answered, the row is read through it",
          refused is None and reading["note"] == "hello", f"note <- {reading.get('note')!r}")

    #: A second row of the SAME workflow must not ask again -- that is A2, on this kind.
    supplied(workflow, {"customer": "grace", "body": "again"}, columns)
    nagged += len(mapped) - 1
    check("A7 a second row does not re-ask", len(mapped) == 1, f"person mapped {len(mapped)}x")

    #: A different workflow wanting the same parameter name is its own question, because
    #: the identity is `<workflow>.<param>` and its column may well be a different one.
    supplied(Workflow(name="other-thing", params=("note",)), sheet, columns)
    check("A7 and another workflow is its own question", mapped == [
        "file-a-note.note", "other-thing.note"], f"asked about {mapped}")

    print(f"\nNAGGED  a settled question asked again : {nagged}   (must be 0)")
    print(f"LOST    a question reached nowhere     : {lost}   (must be 0)")
    print(f"FAILED  cases not matching             : {failed}")
    return 1 if nagged or lost or failed else 0


if __name__ == "__main__":
    sys.exit(run())
