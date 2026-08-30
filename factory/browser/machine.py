"""The BROWSER machine: what the harness and the factory are handed.

THE ONLY THING IN THIS TREE THAT TOUCHES CDP. Everything above it asks for acts by role and
name and receives typed evidence; nothing above it knows a protocol, a session or a node.

Every act travels and every act is checked, by construction rather than by remembering to:
a press goes through the hand and the guard, and what the page fetched for itself is
collected the whole time.

Playwright supplies attach, transport, page lifecycle and bodies. It does not supply
resolution -- `Accessibility.queryAXTree` returns the node id the guard needs, where a
locator returns a handle -- and it does not supply acts.
"""

from __future__ import annotations

from typing import Any

from factory.browser import bodies as bodies_mod
from factory.browser import locate, session
from factory.browser.guard import press as press_guarded
from factory.browser.hand import Hand, Pace
from factory.core.evidence import Delivery, Did, Exchange
from factory.core.machines import Chooses
from factory.core.workflow import Target


class Machine:
    """One attached browser, driven."""

    def __init__(self, attached: session.Attached, hand: Hand) -> None:
        self._at = attached
        self.hand = hand
        self.bodies = bodies_mod.Bodies()

    @classmethod
    async def attach(cls, cdp_url: str, *, seed: int | None = None,
                     pace: Pace | None = None) -> Machine:
        """`pace` is where a fit of the operator's own rhythm arrives.

        It is operator-scope rather than workflow-scope: how somebody drives a browser is a
        property of them and their machine. With none supplied the defaults stand, and the
        driver neither knows nor cares which it got.
        """
        attached = await session.attach(cdp_url)
        machine = cls(attached, Hand(seed=seed, pace=pace or Pace()))
        await attached.cdp.send("Network.enable", {})
        machine.bodies.watch(attached.cdp)
        return machine

    @property
    def cdp(self) -> Any:
        return self._at.cdp

    async def _document(self) -> int:
        """The current document's node id. Asked every time: ids do not survive a navigation."""
        got = await self.cdp.send("DOM.getDocument", {"depth": -1})
        return got["root"]["nodeId"]

    async def see(self) -> list[dict[str, Any]]:
        """The candidate set: every accessibility node the page is offering.

        Measured at 1.8 ms, against 10 ms for an agent framework's own serialisation which
        also omitted a control carrying the exact role and name being searched for.
        """
        got = await self.cdp.send("Accessibility.getFullAXTree", {})
        return [node for node in got.get("nodes", []) if not node.get("ignored")]

    async def find(self, target: Target, chooser: Chooses | None = None) -> locate.Found:
        """Rung 0, then the chooser, then a question. Descends only on a miss.

        The chooser is the model, and it is optional: with none supplied the driver still
        works and still says why it could not proceed, rather than pretending it can.
        """
        asked: dict[str, Any] = {"nodeId": await self._document()}
        if target.role:
            asked["role"] = target.role
        if target.name:
            asked["accessibleName"] = target.name
        hits = (await self.cdp.send("Accessibility.queryAXTree", asked)).get("nodes", [])

        every = await self.see()
        offered = locate.offered(every)
        found = locate.settle(hits, target, offered)
        if found or chooser is None:
            return found

        picked = chooser(target, offered)
        if picked is None or not (0 <= picked < len(every)):
            return found
        chosen = locate.reads(every[picked])[2]
        if chosen is None:
            return found
        return locate.Found(backend_node_id=chosen, rung="chosen",
                            why=f"chose {offered[picked]}", among=offered)

    async def go(self, url: str) -> Did:
        """Navigation, waited for and checked rather than assumed.

        A navigation returns without raising when a server redirects to a login or an error
        page, so a step that only asks whether the call threw reports arriving somewhere it
        never went.
        """
        await self._at.page.goto(url, wait_until="load")
        landed = str(await self.evaluate("location.href") or "")
        arrived = landed.split("#")[0].rstrip("/") == url.split("#")[0].rstrip("/")
        return Did(ok=arrived, value=landed,
                   detail=f"go {url}" if arrived else f"asked for {url}, tab is at {landed}")

    async def press(self, found: locate.Found) -> Did:
        """Travel to an already-located target, re-measure there, act only if it holds.

        Separate from `find` because the harness locates once and may act later, and the
        whole point of the guard is that the world can change in between.
        """
        if not found:
            return Did(ok=False, delivery=Delivery.NOT_PROBED, detail=found.why)
        landed = await press_guarded(self.cdp, found.backend_node_id, hand=self.hand)
        await self.hand.rest()
        return Did(ok=landed.dispatched, delivery=landed.delivery, value=str(landed.moves),
                   detail=f"pressed via {found.rung}" if landed.dispatched
                          else f"refused: {landed.why}")

    async def click(self, target: Target, chooser: Chooses | None = None) -> Did:
        """Find it and press it."""
        return await self.press(await self.find(target, chooser))

    async def type(self, text: str) -> Did:
        """Key by key, into whatever holds focus, the way a keyboard delivers it.

        THREE EVENTS PER CHARACTER, NOT ONE. `type: char` alone fires `keypress` and
        `input` and never `keydown` -- measured: ten characters typed and the page's own
        keydown listener saw zero. Text appearing with no keystrokes behind it is exactly
        what a behavioural detector looks for.
        """
        for character in text:
            for kind in ("keyDown", "char", "keyUp"):
                await self.cdp.send("Input.dispatchKeyEvent",
                                    {"type": kind, "text": character, "key": character})
            await self.hand.rest_key()
        return Did(ok=True, value=text, detail=f"typed {len(text)} characters")

    async def evaluate(self, expression: str) -> Any:
        """Reading the page. Never a way to act on it -- acts go through the guard."""
        return await self._at.page.evaluate(expression)

    async def fetched(self) -> list[Exchange]:
        """What the page fetched for itself since the last time this was asked."""
        return await self.bodies.drain(self.cdp)

    async def close(self) -> None:
        await self._at.close()
