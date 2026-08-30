"""Role and name, out of the vendor's own serialisation. Refuses on zero or two-plus.

Acting on the wrong control is indistinguishable from working until something lands in
the wrong field, so a locate that cannot be sure returns nothing rather than the first
match. Ambiguity is reported with the candidates, because the answer to it is a question
for a person or a model, not a rule written here.
"""

from __future__ import annotations

from typing import Any, NamedTuple


class Found(NamedTuple):
    """One resolved control, or why it could not be resolved."""

    backend_node_id: int | None
    why: str
    candidates: tuple[str, ...] = ()

    def __bool__(self) -> bool:
        return self.backend_node_id is not None


def _label(node: Any) -> tuple[str, str]:
    ax = getattr(node, "ax_node", None)
    role = (getattr(ax, "role", None) or node.node_name or "").lower()
    name = (getattr(ax, "name", None) or "").strip()
    return role, name


async def visible(session: Any) -> dict[int, Any]:
    """Every interactive element the vendor could serialise, by its index."""
    state = await session.get_browser_state_summary(include_screenshot=False)
    return dict(state.dom_state.selector_map)


def among(nodes: dict[int, Any], role: str, name: str) -> Found:
    """Match on accessible role and name. Both are compared case-insensitively."""
    want_role, want_name = role.strip().lower(), name.strip().lower()
    hits = [
        node for node in nodes.values()
        if (not want_role or _label(node)[0] == want_role)
        and (not want_name or _label(node)[1].lower() == want_name)
    ]
    if not hits:
        seen = {f"{r}={n!r}" for r, n in map(_label, nodes.values()) if n}
        return Found(None, "no match", tuple(sorted(seen))[:20])
    if len(hits) > 1:
        return Found(None, f"{len(hits)} matches",
                     tuple(f"{r}={n!r}" for r, n in map(_label, hits)))
    return Found(hits[0].backend_node_id, "one match")


async def locate(session: Any, role: str, name: str) -> Found:
    return among(await visible(session), role, name)
