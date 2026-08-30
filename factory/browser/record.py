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
import contextlib
import json
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel, Field

from factory.browser import locate, surface
from factory.browser.bodies import Bodies
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

SETTLE = 20

REPORT = """
(() => {
  if (window.__factory_acts) return;
  window.__factory_acts = true;
  const say = (act) => { try { __factory_act(JSON.stringify(act)); } catch (e) {} };
  const secret = (el) => {
    if (el.type === 'password') return true;
    const how = (el.getAttribute('autocomplete') || '').toLowerCase();
    return how === 'current-password' || how === 'new-password';
  };

  const named = (el) =>
    'secret:' + (location.hostname + '-' + (el.name || el.id || 'password'))
      .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

  const at = (el) => {
    const r = el && el.getBoundingClientRect ? el.getBoundingClientRect() : null;
    return r ? { x: r.left + r.width / 2, y: r.top + r.height / 2 } : { x: 0, y: 0 };
  };

  // ONE WRITE PER FIELD, CARRYING WHAT IT ENDED UP HOLDING, emitted before whatever act
  // ends it. `change` fires on BLUR, so a write recorded there landed after the press that
  // moved focus away and the induced program pressed Save on an empty field. Measured.
  let writing = null;
  const flush = () => { if (writing) { say(writing.act); writing = null; } };

  addEventListener('input', e => {
    const el = e.target;
    if (!el || !('value' in el)) return;
    // A SELECT IS NOT TYPING. Both raise `input`, and recording a pick as a write replays
    // it by typing the option's text into a control that has no text.
    if (el.tagName === 'SELECT') {
      flush();
      say({ doing: 'select', ...at(el), value: String(el.value) });
      return;
    }
    const kept = secret(el) ? named(el) : String(el.value);
    if (writing && writing.on === el) { writing.act.value = kept; return; }
    flush();
    writing = { on: el, act: { doing: 'write', ...at(el), value: kept } };
  }, true);

  addEventListener('mousedown', e => {
    flush();
    say({ doing: 'press', x: e.clientX, y: e.clientY });
  }, true);

  // KEYS THAT ARE NOT TEXT. A character is already a write; Tab, Enter and Escape are acts
  // in their own right and a form filled by tabbing records nothing without this.
  addEventListener('keydown', e => {
    if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) return;
    flush();
    say({ doing: 'key', ...at(e.target), value: e.key });
  }, true);

  // SCROLLING, COALESCED. One act per resting place rather than one per pixel: what
  // matters is where they ended up, not the hundred events on the way.
  let resting = null;
  addEventListener('scroll', () => {
    clearTimeout(resting);
    resting = setTimeout(() => say({
      doing: 'scroll', x: 0, y: 0, value: String(Math.round(window.scrollY)) }), 350);
  }, true);

  addEventListener('blur', flush, true);
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


async def _offered(cdp: Any) -> tuple[str, ...]:
    """Everything the page was offering, described the way `locate` describes it.

    ASKED WITH THE SAME FUNCTION REPLAY USES. Two describers would let a recorded
    candidate set and a resolved one disagree, and the disagreement would look like the
    page having changed.
    """
    try:
        tree = await cdp.send("Accessibility.getFullAXTree", {})
    except Exception:
        return ()
    return tuple(sorted(locate.offered(tree.get("nodes", [])).values()))


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


async def acts(context: Any, into: list[Act]) -> Callable[[], Awaitable[list[Any]]]:
    """Report every act a person performs on ANY surface, as it happens.

    EVERY PAGE, AND EVERY PAGE OPENED LATER. Installed on one page this recorded a fifth of
    a five-tab task and produced a ledger that looked complete -- measured: an act on a
    second surface left no trace at all while its request reached the server.

    THE RESOLUTION RUNS OFF THE HANDLER. Awaiting a CDP request inside a handler for an
    event on the same connection hangs forever -- the rule `browser/bodies.py` records. The
    handler starts a task; the task asks the page what it just touched.
    """
    watching: set[Any] = set()
    #: Every page's collector, so recording can be CLOSED. The last act's effect arrives
    #: after it and has no next act to land on; this is where it is taken instead.
    collectors: list[tuple[Any, Bodies]] = []

    async def attach(page: Any) -> None:
        if page in watching:
            return
        watching.add(page)
        cdp = await context.new_cdp_session(page)
        await cdp.send("Runtime.enable", {})
        await cdp.send("Runtime.addBinding", {"name": ACTS})
        #: ONE COLLECTOR PER SURFACE, THE SAME WAY ONE RECORDER PER SURFACE. A `Bodies`
        #: reads request ids off the session that saw them, so a single one attached to
        #: the first page would collect a fifth of a five-tab demonstration -- the defect
        #: acts already had, in the half that carries the evidence.
        kept = Bodies()
        await cdp.send("Network.enable", {})
        kept.watch(cdp)
        collectors.append((cdp, kept))

        def reported(message: dict[str, Any]) -> None:
            if message.get("name") != ACTS:
                return
            said = json.loads(message.get("payload") or "{}")
            where = (said.get("x", 0), said.get("y", 0))

            #: THE SLOT IS TAKEN NOW, THE DESCRIPTION ARRIVES LATER. Resolution is three
            #: CDP round trips and appending when it finishes puts acts in COMPLETION
            #: order: measured, a press and the press after it landed reversed, and
            #: `compile/mine.events` reads a demonstration in list order. Two handlers
            #: cannot interleave -- they run on the loop -- so the index is the order the
            #: person acted in, whatever order the answers come back in.
            slot = len(into)
            into.append(Act(doing=Doing(said["doing"]),
                            value=str(said.get("value", "")),
                            surface=surface.of(page.url), where=where))

            async def resolve() -> None:
                #: DRAINED FIRST, BEFORE ANYTHING IS ASKED OF THE PAGE. A response is
                #: assigned to an act by when it arrived, so every round trip spent here
                #: first is a window in which this act swallows its own effect -- and an
                #: effect inside its own `sor_before` is a delta of nothing. That costs a
                #: contract and never produces a wrong one, which is the direction this
                #: has to fail in.
                saw = await kept.drain(cdp)
                target = await _named(cdp, *where)
                into[slot] = into[slot].model_copy(update={
                    "target": target, "saw": saw, "among": await _offered(cdp)})

            asyncio.get_running_loop().create_task(resolve())

        cdp.on("Runtime.bindingCalled", reported)
        await page.add_init_script(REPORT)
        #: A page still navigating has no context to evaluate in yet; the init script
        #: installed above catches it when it does.
        with contextlib.suppress(Exception):
            await page.evaluate(REPORT)

    for page in list(context.pages):
        await attach(page)

    #: A surface opened after recording started is one the person chose to open, which is
    #: the ordinary case in a task that spans tools.
    context.on("page", lambda page: asyncio.get_running_loop().create_task(attach(page)))

    async def close() -> list[Any]:
        for _ in range(SETTLE):
            if not any(kept.waiting() for _, kept in collectors):
                break
            await asyncio.sleep(0.1)
        drained: list[Any] = []
        for cdp, kept in collectors:
            with contextlib.suppress(Exception):
                drained.extend(await kept.drain(cdp))
        return drained

    return close


async def drain(page: Any) -> Watched:
    """Take what the page has collected and leave it empty."""
    got = await page.evaluate(DRAIN)
    return Watched(**got) if got else Watched()
