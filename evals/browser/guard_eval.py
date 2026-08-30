"""Run the four guard fixtures against a real browser and print both scores.

    uv run python -m evals.browser.guard_eval

Each case locates the element FIRST, then changes the page, then presses -- which is the
real sequence, since a guard measures at dispatch time and not at locate time.
"""

from __future__ import annotations

import asyncio
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from factory.browser import profile, session
from factory.browser.guard import press
from factory.core.evidence import Delivery

FIXTURE = Path(__file__).parent / "fixtures" / "guard.html"
PORT = 9333

#: name -> (selector, page change applied after locating, expected delivery, expect dispatch)
CASES = (
    ("F1 impostor swap", "#target",
     "const n=document.createElement('button');n.id='target';"
     "document.getElementById('target').replaceWith(n);",
     Delivery.OFF_TARGET, False),
    ("F2 consent overlay", "#target",
     "document.getElementById('veil').style.display='block';",
     Delivery.INTERCEPTED, False),
    ("F3 label for hidden input", "#real",
     "",
     Delivery.TARGET_HIT, True),
    # KNOWN LIMIT, recorded rather than hidden: an input with display:none has no box,
    # so no point on it is computable and the guard refuses. Targeting its label is
    # locate's job, not the guard's.
    ("F5 boxless input", "#boxless", "", Delivery.OFF_TARGET, False),
    ("F4 target off viewport", "#target",
     "document.getElementById('target').style.position='fixed';"
     "document.getElementById('target').style.top='-500px';",
     Delivery.OFF_TARGET, False),
)


async def _node(cdp: Any, sid: str, selector: str) -> int:
    doc = await cdp.send.DOM.getDocument(params={"depth": -1}, session_id=sid)
    found = await cdp.send.DOM.querySelector(
        params={"nodeId": doc["root"]["nodeId"], "selector": selector}, session_id=sid)
    described = await cdp.send.DOM.describeNode(
        params={"nodeId": found["nodeId"]}, session_id=sid)
    return described["node"]["backendNodeId"]


async def run() -> int:
    home = Path(tempfile.mkdtemp(prefix="factory-guard-"))
    browser = profile.launch(home / "profile", PORT)
    safety = liveness = 0
    try:
        for _ in range(40):
            try:
                url = session.endpoint(PORT)
                break
            except OSError:  # the browser has not opened the port yet
                await asyncio.sleep(0.25)
        else:
            raise RuntimeError("browser never opened its debugging port")

        live = await session.attach(url)
        cdp = await live.get_or_create_cdp_session()

        for name, selector, change, expected, should_dispatch in CASES:
            await cdp.cdp_client.send.Page.navigate(
                params={"url": FIXTURE.as_uri()}, session_id=cdp.session_id)
            await asyncio.sleep(0.6)

            node = await _node(cdp.cdp_client, cdp.session_id, selector)
            if change:
                await cdp.cdp_client.send.Runtime.evaluate(
                    params={"expression": change}, session_id=cdp.session_id)

            landed = await press(cdp.cdp_client, cdp.session_id, node)
            got = await cdp.cdp_client.send.Runtime.evaluate(
                params={"expression": "JSON.stringify(window.__clicks)", "returnByValue": True},
                session_id=cdp.session_id)
            clicks = got["result"].get("value", "[]")

            ok = landed.delivery == expected and landed.dispatched == should_dispatch
            if landed.dispatched and not should_dispatch:
                safety += 1
            if should_dispatch and not landed.dispatched:
                liveness += 1
            print(f"{'ok  ' if ok else 'FAIL'} {name:26} "
                  f"delivery={landed.delivery:<12} dispatched={landed.dispatched!s:<5} "
                  f"why={landed.why:<16} page_saw={clicks}")

        await live.stop()
    finally:
        browser.terminate()
        shutil.rmtree(home, ignore_errors=True)

    print(f"\nSAFETY   dispatched when it should have refused : {safety}   (must be 0)")
    print(f"LIVENESS refused when it should have dispatched  : {liveness}")
    return 1 if safety or liveness else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
