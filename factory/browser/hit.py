"""Is the intended element the one actually at the point we would press?

Computed in the page, so the guard point and the press point are the same number rather
than two computations that agree by luck. The point is produced once by `where` and then
passed to travel, to `at_point` and to dispatch -- one value, three uses.
"""

from __future__ import annotations

from typing import Any

#: Runs with the element as `this`. Returns a point on its current box, or nothing if it
#: has no box to compute one from.
WHERE = """
function (fx, fy) {
  if (!this.isConnected) return null;
  const r = this.getBoundingClientRect();
  if (!r.width || !r.height) return null;
  return { x: r.left + r.width * fx, y: r.top + r.height * fy };
}
"""

#: Runs with the element as `this`, at an ALREADY CHOSEN point.
#:
#: AN ANCESTOR IS NOT A HIT. `at.contains(this)` was here and is always true when
#: elementFromPoint returns <body>, so an element that had moved away was approved --
#: measured, on a target that leaves on mouseover.
#:
#: A LABEL STANDS FOR ITS INPUT. A styled checkbox paints the <label> over the real
#: <input>, so elementFromPoint returns the label, and plain containment refuses a correct
#: press.
AT_THE_POINT = """
function (x, y) {
  if (!this.isConnected) return { hit: false, reason: 'gone' };
  if (x < 0 || y < 0 || x > innerWidth || y > innerHeight)
    return { hit: false, reason: 'outside' };

  const at = document.elementFromPoint(x, y);
  if (!at) return { hit: false, reason: 'outside' };
  if (at === this || this.contains(at))
    return { hit: true, reason: 'self', tag: at.tagName };

  const label = at.closest('label');
  if (label && (label.control === this ||
                (label.htmlFor && document.getElementById(label.htmlFor) === this)))
    return { hit: true, reason: 'label', tag: at.tagName };

  return { hit: false, reason: 'covered', tag: at.tagName };
}
"""


async def _call(cdp: Any, object_id: str, fn: str, args: tuple[Any, ...]) -> Any:
    answer = await cdp.send("Runtime.callFunctionOn", {
        "functionDeclaration": fn,
        "objectId": object_id,
        "arguments": [{"value": arg} for arg in args],
        "returnByValue": True,
    })
    return answer["result"].get("value")


async def where(cdp: Any, object_id: str, fx: float, fy: float
                ) -> tuple[float, float] | None:
    """A point on the element's box, chosen once."""
    got = await _call(cdp, object_id, WHERE, (fx, fy))
    return (got["x"], got["y"]) if got else None


async def at_point(cdp: Any, object_id: str, x: float, y: float) -> dict[str, Any]:
    """What is at that exact point, now."""
    return await _call(cdp, object_id, AT_THE_POINT, (x, y)) or {}
