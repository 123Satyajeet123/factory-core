"""Refuse, then dispatch. Ours, and no vendor supplies it.

Playwright refuses a covered target by TIMEOUT, and a timeout is indistinguishable from a
slow page -- one exception meaning three things. browser-use detects occlusion and then
dispatches `this.click()` through it, which reads as safety in the log. So the decision to
send lives here and returns a typed answer.

REACH, THEN MEASURE, THEN PRESS, and that order is the point. Moving the pointer changes
what is under it -- a hover menu is the ordinary case -- so a guard that measured before
travelling would approve a target the pointer then left.
"""

from __future__ import annotations

import contextlib
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


async def press(cdp: Any, backend_node_id: int, *, hand: Hand | None = None,
                button: str = "left") -> Landed:
    """Travel to the target, re-measure there, and send nothing if the answer is no.

    Where in the target to land is the hand's to choose. A constant centre is a tell on its
    own: two presses on one control land on the same pixel.
    """
    hand = hand or Hand()
    fx, fy = hand.aim()

    resolved = await cdp.send("DOM.resolveNode", {"backendNodeId": backend_node_id})
    object_id = resolved.get("object", {}).get("objectId")
    if not object_id:
        return Landed(dispatched=False, delivery=Delivery.OFF_TARGET, why="unresolvable")

    #: BRING IT INTO VIEW FIRST. Refusing an off-viewport target is right for a guard and
    #: useless as a capability: a person scrolls to what they mean to press. This is a
    #: no-op when the control is already visible, and the guard still measures afterwards,
    #: so scrolling cannot smuggle a press onto something that moved.
    with contextlib.suppress(Exception):
        await cdp.send("DOM.scrollIntoViewIfNeeded", {"backendNodeId": backend_node_id})
        await hand.settle()

    point = await where(cdp, object_id, fx, fy)
    if point is None:
        return Landed(dispatched=False, delivery=Delivery.OFF_TARGET, why="no box")

    moves = await hand.reach(cdp, point)

    seen = await at_point(cdp, object_id, *point)
    if not seen.get("hit"):
        reason = seen.get("reason", "covered")
        return Landed(dispatched=False, delivery=_REFUSALS.get(reason, Delivery.INTERCEPTED),
                      why=f"{reason} {seen.get('tag', '')}".strip(), at=point, moves=moves)

    await hand.press_at(cdp, point, button)
    return Landed(dispatched=True, delivery=Delivery.TARGET_HIT,
                  why=seen["reason"], at=point, moves=moves)
