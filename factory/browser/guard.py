"""Refuse, then dispatch. Ours, beside hit.py.

Not a vendor extension. browser_use's default_action_watchdog.py:876 and :1815 both do
`if is_occluded -> Runtime.callFunctionOn "function(){this.click();}"` -- detection whose
consequence is dispatch anyway -- so clicks do not go through its ClickElementEvent.

REACH, THEN MEASURE, THEN PRESS, and that order is the point. Moving the pointer changes
what is under it -- a hover menu is the ordinary case -- so a guard that measured before
travelling would approve a target the pointer then left.
"""

from __future__ import annotations

from typing import Any

from factory.browser.hand import Hand
from factory.browser.hit import at_point, where
from factory.core.evidence import Delivery, Landed

#: reason from AT_THE_POINT -> why nothing was sent.
_REFUSALS = {
    "gone": Delivery.OFF_TARGET,
    "outside": Delivery.OFF_TARGET,
    "covered": Delivery.INTERCEPTED,
}


async def press(cdp: Any, session_id: str, backend_node_id: int, *,
                hand: Hand | None = None, fx: float = 0.5, fy: float = 0.5,
                button: str = "left") -> Landed:
    """Travel to the target, re-measure there, and send nothing if the answer is no."""
    hand = hand or Hand()

    resolved = await cdp.send.DOM.resolveNode(
        params={"backendNodeId": backend_node_id}, session_id=session_id)
    object_id = resolved.get("object", {}).get("objectId")
    if not object_id:
        return Landed(dispatched=False, delivery=Delivery.OFF_TARGET, why="unresolvable")

    point = await where(cdp, session_id, object_id, fx, fy)
    if point is None:
        return Landed(dispatched=False, delivery=Delivery.OFF_TARGET, why="no box")

    moves = await hand.reach(cdp, session_id, point)

    seen = await at_point(cdp, session_id, object_id, *point)
    if not seen.get("hit"):
        reason = seen.get("reason", "covered")
        return Landed(dispatched=False, delivery=_REFUSALS.get(reason, Delivery.INTERCEPTED),
                      why=f"{reason} {seen.get('tag', '')}".strip(), at=point, moves=moves)

    await hand.press_at(cdp, session_id, point, button)
    return Landed(dispatched=True, delivery=Delivery.TARGET_HIT,
                  why=seen["reason"], at=point, moves=moves)
