"""Refuse, then dispatch. Ours, beside hit.py.

Not a vendor extension. browser_use's default_action_watchdog.py:876 and :1815 both do
`if is_occluded -> Runtime.callFunctionOn "function(){this.click();}"` -- detection whose
consequence is dispatch anyway -- so clicks do not go through its ClickElementEvent.
"""

from __future__ import annotations

from typing import Any

from factory.browser.hit import probe
from factory.core.evidence import Delivery, Landed

#: reason from AT_THE_POINT -> why nothing was sent.
_REFUSALS = {
    "gone": Delivery.OFF_TARGET,
    "outside": Delivery.OFF_TARGET,
    "covered": Delivery.INTERCEPTED,
}


async def press(cdp: Any, session_id: str, backend_node_id: int, *,
                fx: float = 0.5, fy: float = 0.5, button: str = "left") -> Landed:
    """Measure immediately before dispatch, and send nothing if the answer is no."""
    resolved = await cdp.send.DOM.resolveNode(
        params={"backendNodeId": backend_node_id}, session_id=session_id)
    object_id = resolved.get("object", {}).get("objectId")
    if not object_id:
        return Landed(dispatched=False, delivery=Delivery.OFF_TARGET, why="unresolvable")

    seen = await probe(cdp, session_id, object_id, fx, fy)
    at = (seen["x"], seen["y"]) if "x" in seen else None

    if not seen.get("hit"):
        reason = seen.get("reason", "covered")
        return Landed(dispatched=False, delivery=_REFUSALS.get(reason, Delivery.INTERCEPTED),
                      why=f"{reason} {seen.get('tag', '')}".strip(), at=at)

    x, y = seen["x"], seen["y"]
    for kind in ("mousePressed", "mouseReleased"):
        await cdp.send.Input.dispatchMouseEvent(
            params={"type": kind, "x": x, "y": y, "button": button, "clickCount": 1},
            session_id=session_id)
    return Landed(dispatched=True, delivery=Delivery.TARGET_HIT, why=seen["reason"], at=at)
