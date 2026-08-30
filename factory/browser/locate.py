"""Finding the demonstrated control on the page as it is now.

Rung 0 asks the accessibility tree for the recorded role and name and refuses unless the
answer is unique. The descent to a model, to pixels, and finally to a question belongs to
the caller: deciding which candidate is the demonstrated one is not this driver's job.

REFUSING IS AN ANSWER. Acting on the wrong control is indistinguishable from working until
something lands in the wrong field, so zero matches and two matches are both refusals and
neither is a first match.

Nothing here holds a session. It works on the nodes it is handed, so it can be exercised
without a browser.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from factory.core.question import Ask, Question
from factory.core.workflow import Target


class Found(BaseModel):
    """A resolved control, or why it could not be resolved and what was on offer.

    `rung` is not decoration. Without it a cheap wrong answer and an expensive right one
    look identical downstream, and nothing can learn which rung was worth running.
    """

    backend_node_id: int | None = None
    rung: str = ""
    why: str = ""
    among: dict[int, str] = Field(default_factory=dict)
    question: Question | None = None

    def __bool__(self) -> bool:
        return self.backend_node_id is not None


def reads(node: dict[str, Any]) -> tuple[str, str, int | None]:
    """One accessibility node, in the vocabulary a Target is recorded in."""
    return ((node.get("role") or {}).get("value", "") or "",
            (node.get("name") or {}).get("value", "") or "",
            node.get("backendDOMNodeId"))


def described(node: dict[str, Any]) -> str:
    role, name, _ = reads(node)
    return f"{role} {name!r}" if name else role


def offered(nodes: list[dict[str, Any]]) -> dict[int, str]:
    """The candidate set as a chooser sees it: one line each, keyed by position."""
    return {index: described(node) for index, node in enumerate(nodes)
            if not node.get("ignored")}


def settle(hits: list[dict[str, Any]], target: Target,
           among: dict[int, str], rung: str = "accessible") -> Found:
    """One match is an answer. Nothing else is."""
    live = [node for node in hits if not node.get("ignored")]
    if len(live) == 1 and reads(live[0])[2]:
        return Found(backend_node_id=reads(live[0])[2], rung=rung,
                     why="one match", among=among)

    why = "no match" if not live else f"{len(live)} matches"
    return Found(rung=rung, why=why, among=among,
                 question=Question(kind=Ask.TARGET, about=target.described(), because=why,
                                   candidates=tuple(sorted(among.values()))))
