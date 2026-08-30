"""The BROWSER machine: what the harness and the factory are handed.

THE ONLY THING IN THIS TREE THAT TOUCHES CDP. Everything above it asks for acts by role and
name and receives typed evidence; nothing above it knows a protocol, a session id or a node.

Every act travels and every act is checked, by construction rather than by remembering to:
a press goes through the hand and the guard, and what the page fetched for itself is
collected the whole time.
"""

from __future__ import annotations

import asyncio
from typing import Any

from factory.browser import bodies as bodies_mod
from factory.browser import locate, session
from factory.browser.guard import press as press_guarded
from factory.browser.hand import Hand
from factory.core.evidence import Delivery, Did, Exchange
from factory.core.machines import Chooses
from factory.core.workflow import Target


class Machine:
    """One attached browser, driven."""

    def __init__(self, live: Any, cdp: Any, hand: Hand) -> None:
        self._live = live
        self._cdp = cdp
        self.hand = hand
        self.bodies = bodies_mod.Bodies()

    @classmethod
    async def attach(cls, cdp_url: str, *, seed: int | None = None) -> Machine:
        live = await session.attach(cdp_url)
        cdp = await live.get_or_create_cdp_session()
        machine = cls(live, cdp, Hand(seed=seed))
        await cdp.cdp_client.send.Network.enable(session_id=cdp.session_id)
        machine.bodies.watch(cdp.cdp_client)
        return machine

    @property
    def _client(self) -> Any:
        return self._cdp.cdp_client

    @property
    def _session(self) -> str:
        return self._cdp.session_id

    async def see(self) -> dict[int, Any]:
        """The candidate set: every interactive element the vendor could serialise.

        Fetching candidates is the driver's job and matching them is `locate`'s, so locate
        holds no session and can be exercised without a browser.
        """
        state = await self._live.get_browser_state_summary(include_screenshot=False)
        return dict(state.dom_state.selector_map)

    async def find(self, target: Target, chooser: Chooses | None = None) -> locate.Found:
        """Rung 0, then the chooser, then a question. Descends only on a miss.

        The chooser is the model, and it is optional: with none supplied the driver still
        works and still says why it could not proceed, rather than pretending it can.
        """
        nodes = await self.see()
        found = locate.among(nodes, target)
        if found or chooser is None:
            return found

        picked = chooser(target, found.among)
        if picked is None or picked not in nodes:
            return found
        return locate.Found(backend_node_id=nodes[picked].backend_node_id,
                            rung="chosen", why=f"chose {found.among[picked]}",
                            among=found.among)

    async def go(self, url: str, *, settle: float = 15.0) -> Did:
        """Navigation, checked rather than assumed, and waited for rather than hoped.

        A navigation returns without raising when a server redirects to a login or an error
        page, so a step that only asks whether the call threw reports arriving somewhere it
        never went. `Page.navigate` is also acked before the document exists -- measured:
        the very next call saw zero elements on a page with eleven.
        """
        await self._client.send.Page.navigate(
            params={"url": url}, session_id=self._session)
        deadline = asyncio.get_running_loop().time() + settle
        while asyncio.get_running_loop().time() < deadline:
            if await self.evaluate("document.readyState") == "complete":
                break
            await asyncio.sleep(0.05)
        landed = await self.evaluate("location.href") or ""
        arrived = str(landed).split("#")[0].rstrip("/") == url.split("#")[0].rstrip("/")
        return Did(ok=arrived, value=str(landed),
                   detail=f"go {url}" if arrived else f"asked for {url}, tab is at {landed}")

    async def press(self, found: locate.Found) -> Did:
        """Travel to an already-located target, re-measure there, act only if it holds.

        Separate from `find` because the harness locates once and may act later, and the
        whole point of the guard is that the world can change in between.
        """
        if not found:
            return Did(ok=False, delivery=Delivery.NOT_PROBED, detail=found.why)

        landed = await press_guarded(self._client, self._session, found.backend_node_id,
                                     hand=self.hand)
        await self.hand.rest()
        return Did(ok=landed.dispatched, delivery=landed.delivery,
                   value=str(landed.moves),
                   detail=f"pressed via {found.rung}" if landed.dispatched
                          else f"refused: {landed.why}")

    async def click(self, target: Target, chooser: Chooses | None = None) -> Did:
        """Find it and press it."""
        return await self.press(await self.find(target, chooser))

    async def type(self, text: str) -> Did:
        """Key by key, into whatever holds focus, the way a keyboard delivers it."""
        for character in text:
            for kind in ("keyDown", "keyUp"):
                await self._client.send.Input.dispatchKeyEvent(
                    params={"type": "char" if kind == "keyDown" else kind,
                            "text": character},
                    session_id=self._session)
            await self.hand.rest_key()
        return Did(ok=True, value=text, detail=f"typed {len(text)} characters")

    async def evaluate(self, expression: str) -> Any:
        """Reading the page. Never a way to act on it -- acts go through the guard."""
        got = await self._client.send.Runtime.evaluate(
            params={"expression": expression, "returnByValue": True},
            session_id=self._session)
        return got["result"].get("value")

    async def fetched(self) -> list[Exchange]:
        """What the page fetched for itself since the last time this was asked."""
        return await self.bodies.drain(self._client, self._session)

    async def close(self) -> None:
        await self._live.stop()
