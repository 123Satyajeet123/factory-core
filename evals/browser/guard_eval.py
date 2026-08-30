"""The guard's fixtures, and the shape of the input that carries it.

    uv run python -m evals.browser.guard_eval

See gates/browser-guard.md and gates/human-input.md. Each case locates the element FIRST,
then changes the page, then presses -- the real sequence, since a guard measures at
dispatch time and not at locate time.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from factory.browser import profile, session
from factory.browser.guard import press
from factory.browser.hand import Hand
from factory.core.evidence import Delivery

FIXTURE = Path(__file__).parent / "fixtures" / "guard.html"
PORT = 9333

#: name, selector, page change applied after locating, expected delivery, expect dispatch.
#: A `None` delivery means any refusal will do -- the claim is that nothing was sent.
CASES: tuple[tuple[str, str, str, Delivery | None, bool], ...] = (
    ("F1 impostor swap", "#target",
     "const n=document.createElement('button');n.id='target';"
     "document.getElementById('target').replaceWith(n);",
     Delivery.OFF_TARGET, False),
    ("F2 consent overlay", "#target",
     "document.getElementById('veil').style.display='block';",
     Delivery.INTERCEPTED, False),
    ("F3 label for hidden input", "#real", "", Delivery.TARGET_HIT, True),
    # A limit, recorded rather than hidden: display:none has no box, so no point on it is
    # computable. Targeting its painted label instead is locate's job, not the guard's.
    ("F5 boxless input", "#boxless", "", Delivery.OFF_TARGET, False),
    ("F4 target off viewport", "#target",
     "document.getElementById('target').style.position='fixed';"
     "document.getElementById('target').style.top='-500px';",
     Delivery.OFF_TARGET, False),
    # H2: leaves as the pointer arrives. Refusing this is only possible because the guard
    # measures AFTER travelling.
    ("H2 leaves on hover", "#skittish", "", None, False),
)


async def _node(cdp: Any, sid: str, selector: str) -> int:
    doc = await cdp.send.DOM.getDocument(params={"depth": -1}, session_id=sid)
    found = await cdp.send.DOM.querySelector(
        params={"nodeId": doc["root"]["nodeId"], "selector": selector}, session_id=sid)
    described = await cdp.send.DOM.describeNode(
        params={"nodeId": found["nodeId"]}, session_id=sid)
    return described["node"]["backendNodeId"]


async def _read(cdp: Any, sid: str, expression: str) -> Any:
    got = await cdp.send.Runtime.evaluate(
        params={"expression": expression, "returnByValue": True}, session_id=sid)
    return got["result"].get("value")


async def run() -> int:
    home = Path(tempfile.mkdtemp(prefix="factory-guard-"))
    browser = profile.launch(home / "profile", PORT)
    safety = liveness = shape = 0
    try:
        for _ in range(40):
            try:
                url = session.endpoint(PORT)
                break
            except OSError:
                await asyncio.sleep(0.25)
        else:
            raise RuntimeError("browser never opened its debugging port")

        live = await session.attach(url)
        cdp = await live.get_or_create_cdp_session()
        client, sid = cdp.cdp_client, cdp.session_id

        for name, selector, change, expected, should_dispatch in CASES:
            await client.send.Page.navigate(params={"url": FIXTURE.as_uri()}, session_id=sid)
            await asyncio.sleep(0.6)
            #: Navigating to the same URL does not reliably give a fresh JS context, and a
            #: counter carried between cases reports travel that belonged to the last one.
            await _read(client, sid, "window.__clicks=[];window.__moves=[];0")

            node = await _node(client, sid, selector)
            if change:
                await _read(client, sid, change)

            landed = await press(client, sid, node, hand=Hand(seed=17))
            clicks = json.loads(await _read(client, sid, "JSON.stringify(window.__clicks)"))
            moves = int(await _read(client, sid, "window.__moves.length") or 0)

            delivered_ok = expected is None or landed.delivery == expected
            ok = delivered_ok and landed.dispatched == should_dispatch
            if landed.dispatched and not should_dispatch:
                safety += 1
            if should_dispatch and not landed.dispatched:
                liveness += 1
            # H1, and only where something was sent: a refusal that happens before the
            # pointer travels has nothing to have travelled for.
            if landed.dispatched and moves < 2:
                shape += 1

            print(f"{'ok  ' if ok else 'FAIL'} {name:26} "
                  f"delivery={landed.delivery:<12} dispatched={landed.dispatched!s:<5} "
                  f"moves={moves:<3} why={landed.why:<16} page_saw={clicks}")

        await live.stop()
    finally:
        browser.terminate()
        shutil.rmtree(home, ignore_errors=True)

    print(f"\nSAFETY   dispatched when it should have refused : {safety}   (must be 0)")
    print(f"LIVENESS refused when it should have dispatched  : {liveness}")
    print(f"SHAPE    presses the page saw arrive without travel : {shape}   (must be 0)")
    return 1 if safety or liveness or shape else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
