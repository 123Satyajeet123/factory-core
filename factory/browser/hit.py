"""Is the intended element the one actually at the point we would press?

Computed in the page, and it returns the point it tested, so the guard point and the
press point are the same number rather than two computations that agree by luck.
"""

from __future__ import annotations

from typing import Any

#: Runs with the element as `this`. Returns the point it tested so the caller dispatches
#: at exactly that point.
#:
#: A LABEL STANDS FOR ITS INPUT. A styled checkbox hides the real <input> and paints the
#: <label>, so elementFromPoint returns the label -- not the element, not containing it,
#: not contained by it -- and plain containment refuses a correct press.
AT_THE_POINT = """
function (fx, fy) {
  if (!this.isConnected) return { hit: false, reason: 'gone' };
  const r = this.getBoundingClientRect();
  if (!r.width || !r.height) return { hit: false, reason: 'gone' };

  const x = r.left + r.width * fx;
  const y = r.top + r.height * fy;
  if (x < 0 || y < 0 || x > innerWidth || y > innerHeight)
    return { hit: false, reason: 'outside', x, y };

  const at = document.elementFromPoint(x, y);
  if (!at) return { hit: false, reason: 'outside', x, y };
  if (at === this || this.contains(at) || at.contains(this))
    return { hit: true, reason: 'self', x, y, tag: at.tagName };

  const label = at.closest('label');
  if (label && (label.control === this ||
                (label.htmlFor && document.getElementById(label.htmlFor) === this)))
    return { hit: true, reason: 'label', x, y, tag: at.tagName };

  return { hit: false, reason: 'covered', x, y, tag: at.tagName };
}
"""


async def probe(cdp: Any, session_id: str, object_id: str,
                fx: float = 0.5, fy: float = 0.5) -> dict[str, Any]:
    """Run the rule against one resolved element. Returns its raw answer."""
    answer = await cdp.send.Runtime.callFunctionOn(
        params={
            "functionDeclaration": AT_THE_POINT,
            "objectId": object_id,
            "arguments": [{"value": fx}, {"value": fy}],
            "returnByValue": True,
        },
        session_id=session_id,
    )
    return answer["result"].get("value") or {}
