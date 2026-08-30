"""What a person did, reported by the page itself.

LISTENERS ONLY, AND THAT DISTINCTION IS THE WHOLE SAFETY ARGUMENT. This adds
`addEventListener` calls and one global. It redefines no property, replaces no native
method, and leaves every `toString()` reading `[native code]`. The patches measured to cost
detection signals were the ones that lied about `navigator`; see `stealth.py`.

INSTALLED ONLY WHILE RECORDING, NEVER WHILE DRIVING. A person demonstrating is using their
own browser and the page is being driven by a hand. A replay injects nothing at all, which
is the state the stealth argument is about.

TIMING, NEVER CONTENT. Key events record when, and no key. A store of what was typed is a
password store and this project does not hold those.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from pydantic import BaseModel, Field

from factory.core.ledger import Act, Doing
from factory.core.workflow import Target

#: One global, one name, and nothing else touched. `capture: true` so a page that stops
#: propagation cannot blind the recorder.
WATCH = """
(() => {
  if (window.__factory_watch) return;
  const seen = { moves: [], keys: [], presses: [], releases: [] };
  window.__factory_watch = seen;
  addEventListener('mousemove', e => {
    seen.moves.push([e.clientX, e.clientY, performance.now()]);
    if (seen.moves.length > 20000) seen.moves.splice(0, 10000);
  }, true);
  addEventListener('keydown', () => seen.keys.push(performance.now()), true);
  addEventListener('mousedown', e => {
    const r = e.target && e.target.getBoundingClientRect
      ? e.target.getBoundingClientRect() : null;
    seen.presses.push([
      performance.now(),
      r && r.width ? (e.clientX - r.left) / r.width : null,
      r && r.height ? (e.clientY - r.top) / r.height : null,
    ]);
  }, true);
  addEventListener('mouseup', () => seen.releases.push(performance.now()), true);
})();
"""

#: The page reports an act the moment it happens, through a binding we registered. A
#: timestamped queue drained later would be too late: the accessible name of a control is
#: read from the page as it was, and a page that has moved on reports a different one.
ACTS = "__factory_act"

REPORT = """
(() => {
  if (window.__factory_acts) return;
  window.__factory_acts = true;
  const say = (act) => { try { __factory_act(JSON.stringify(act)); } catch (e) {} };
  addEventListener('mousedown', e => say(
    { doing: 'press', x: e.clientX, y: e.clientY }), true);
  addEventListener('change', e => {
    const r = e.target && e.target.getBoundingClientRect
      ? e.target.getBoundingClientRect() : null;
    if (r && 'value' in e.target) say(
      { doing: 'write', x: r.left + r.width / 2, y: r.top + r.height / 2,
        value: String(e.target.value) });
  }, true);
})();
"""

DRAIN = """
(() => {
  const seen = window.__factory_watch;
  if (!seen) return null;
  const taken = { moves: seen.moves, keys: seen.keys,
                  presses: seen.presses, releases: seen.releases };
  seen.moves = []; seen.keys = []; seen.presses = []; seen.releases = [];
  return taken;
})()
"""


class Watched(BaseModel):
    """Raw timing, as the page reported it. Milliseconds, page-relative."""

    moves: list[tuple[float, float, float]] = Field(default_factory=list)
    keys: list[float] = Field(default_factory=list)
    #: when, and where in the target's box the press landed, as fractions.
    presses: list[tuple[float, float | None, float | None]] = Field(default_factory=list)
    releases: list[float] = Field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.moves or self.keys or self.presses)


async def watch(page: Any) -> None:
    """Start listening, and keep listening across navigations."""
    await page.add_init_script(WATCH)
    await page.evaluate(WATCH)


#: A LABEL STANDS FOR ITS INPUT, HERE TOO. `hit.py` allows a press to land on the label a
#: styled control paints; this is the same rule from the recording side. The topmost node at
#: a point is the label, and recording that gives `LabelText` with no name -- measured: two
#: matches, findable again by nothing.
STANDS_FOR = "function () { return (this.control || this.htmlFor && "\
             "document.getElementById(this.htmlFor)) || this; }"


async def _actionable(cdp: Any, node: int) -> int:
    """The node a press on this one is really aimed at."""
    try:
        held = await cdp.send("DOM.resolveNode", {"backendNodeId": node})
        object_id = held.get("object", {}).get("objectId")
        if not object_id:
            return node
        stands = await cdp.send("Runtime.callFunctionOn",
                                {"functionDeclaration": STANDS_FOR, "objectId": object_id})
        target = stands.get("result", {}).get("objectId")
        if not target:
            return node
        asked = await cdp.send("DOM.describeNode", {"objectId": target})
        return int(asked["node"]["backendNodeId"]) or node
    except Exception:
        return node


async def _named(cdp: Any, x: float, y: float) -> Target | None:
    """What the page calls the control at that point, asked of the accessibility tree.

    Not computed from tag names in the page: the accessible name has a specification, and
    the one that matters is the one `locate` will search for on replay. Asking the same
    tree that will be searched is the only way those agree.
    """
    try:
        at = await cdp.send("DOM.getNodeForLocation",
                            {"x": int(x), "y": int(y), "includeUserAgentShadowDOM": False})
        node = at.get("backendNodeId")
        if not node:
            return None
        node = await _actionable(cdp, node)
        tree = await cdp.send("Accessibility.getPartialAXTree",
                              {"backendNodeId": node, "fetchRelatives": False})
    except Exception:
        return None
    for found in tree.get("nodes", []):
        if found.get("ignored"):
            continue
        role = (found.get("role") or {}).get("value", "")
        name = (found.get("name") or {}).get("value", "")
        if role:
            return Target(role=str(role), name=str(name))
    return None


async def acts(page: Any, cdp: Any, into: list[Act]) -> None:
    """Report every act a person performs into `into`, as it happens.

    THE RESOLUTION RUNS OFF THE HANDLER. Awaiting a CDP request inside a handler for an
    event on the same connection hangs forever -- the same rule `browser/bodies.py` records.
    The handler starts a task; the task asks the page what it just touched.
    """
    await cdp.send("Runtime.addBinding", {"name": ACTS})

    def reported(message: dict[str, Any]) -> None:
        if message.get("name") != ACTS:
            return
        said = json.loads(message.get("payload") or "{}")

        async def resolve() -> None:
            target = await _named(cdp, said.get("x", 0), said.get("y", 0))
            into.append(Act(doing=Doing(said["doing"]), target=target,
                            value=str(said.get("value", "")),
                            where=(said.get("x"), said.get("y"))))

        asyncio.get_running_loop().create_task(resolve())

    cdp.on("Runtime.bindingCalled", reported)
    await page.add_init_script(REPORT)
    await page.evaluate(REPORT)


async def drain(page: Any) -> Watched:
    """Take what the page has collected and leave it empty."""
    got = await page.evaluate(DRAIN)
    return Watched(**got) if got else Watched()
