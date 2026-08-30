"""The one input vocabulary, shared by every producer and every consumer.

A ledger records these, a workflow is made of these, and the BROWSER driver is told these.
One enum rather than three that agree by inspection: three would disagree the first time
one of them grew a member.
"""

from __future__ import annotations

from enum import StrEnum


class Doing(StrEnum):
    """What kind of thing was done, or is to be done. What a browser can be told, no more."""

    PRESS = "press"
    WRITE = "write"
    GO = "go"
    #: A person scrolls, picks from a list, and presses keys that are not text. A ledger
    #: with only the first three is not shorter than what happened -- it is WRONG, and
    #: nothing marks the hole, so the compiler induces a program confidently missing them.
    SCROLL = "scroll"
    SELECT = "select"
    KEY = "key"
    #: A dialog a person answered. Replaying it as silence is answering it differently.
    ANSWER = "answer"
