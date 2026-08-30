"""Finding the demonstrated control on the page as it is now.

Rung 0 only. It matches recorded evidence structurally and refuses when the answer is not
unique; the descent to a model, to pixels, and finally to a question belongs to the caller,
because deciding which candidate is the demonstrated one is not this machine's job.

REFUSING IS AN ANSWER. Acting on the wrong control is indistinguishable from working until
something lands in the wrong field, so zero matches and two matches are both refusals and
neither is a first-match.
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


def described(node: Any) -> str:
    """One line for a node, in the vocabulary a Target is recorded in."""
    ax = getattr(node, "ax_node", None)
    role = (getattr(ax, "role", None) or node.node_name or "").lower()
    name = (getattr(ax, "name", None) or "").strip()
    return f"{role} {name!r}" if name else role


def _fields(node: Any) -> tuple[str, str, str]:
    ax = getattr(node, "ax_node", None)
    return ((getattr(ax, "role", None) or "").strip().lower(),
            (getattr(ax, "name", None) or "").strip().lower(),
            (node.node_name or "").strip().lower())


def matching(nodes: dict[int, Any], target: Target) -> list[int]:
    """Every candidate consistent with what was recorded. Empty fields do not constrain."""
    want = (target.role.strip().lower(), target.name.strip().lower(),
            target.tag.strip().lower())
    hits = []
    for index, node in nodes.items():
        role, name, tag = _fields(node)
        if want[0] and role != want[0]:
            continue
        if want[1] and name != want[1]:
            continue
        if want[2] and tag != want[2]:
            continue
        hits.append(index)
    return hits


def among(nodes: dict[int, Any], target: Target) -> Found:
    """Rung 0. One match is an answer; nothing else is."""
    offered = {index: described(node) for index, node in nodes.items()}
    hits = matching(nodes, target)

    if len(hits) == 1:
        return Found(backend_node_id=nodes[hits[0]].backend_node_id,
                     rung="structural", why="one match", among=offered)

    why = "no match" if not hits else f"{len(hits)} matches"
    return Found(rung="structural", why=why, among=offered,
                 question=Question(kind=Ask.TARGET, about=target.described(), because=why,
                                   candidates=tuple(sorted(offered.values()))))
