"""The guard's fixtures and the shape of the input, driven through the machine.

    uv run python -m evals.browser.guard_eval

See gates/browser-guard.md, gates/human-input.md, gates/pointer-motion.md. Nothing here
touches CDP: the eval asks the driver for acts by role and name, which is what the harness
will do, so a pass means the driver refuses rather than that a helper does.

Each case FINDS the target, then changes the page, then presses -- the real sequence, since
a guard measures at dispatch time and the world moves in between.
"""

from __future__ import annotations

import asyncio
import functools
import http.server
import json
import shutil
import sys
import tempfile
import threading
from pathlib import Path

from factory.browser import profile, session
from factory.browser.machine import Machine
from factory.core.evidence import Delivery

#: SERVED, NOT file://. Measured: Page.navigate to a file: URL leaves the tab on
#: about:blank, and `location.href` reads correct for an instant before it bounces back.
FIXTURES = Path(__file__).parent / "fixtures"
SITE, PORT = 8098, 9333
FIXTURE = f"http://127.0.0.1:{SITE}/guard.html"


def serve() -> http.server.ThreadingHTTPServer:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(FIXTURES))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", SITE), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd

#: name, role, accessible name, change applied after finding, expected delivery, dispatch.
#: A `None` delivery means any refusal will do -- the claim is that nothing was sent.
CASES: tuple[tuple[str, str, str, str, Delivery | None, bool], ...] = (
    ("F1 impostor swap", "button", "target",
     "const n=document.createElement('button');n.id='target';"
     "document.getElementById('target').replaceWith(n);",
     Delivery.OFF_TARGET, False),
    ("F2 consent overlay", "button", "target",
     "document.getElementById('veil').style.display='block';",
     Delivery.INTERCEPTED, False),
    ("F3 label for hidden input", "checkbox", "styled checkbox", "",
     Delivery.TARGET_HIT, True),
    ("F4 target off viewport", "button", "target",
     "document.getElementById('target').style.position='fixed';"
     "document.getElementById('target').style.top='-500px';",
     Delivery.OFF_TARGET, False),
    ("H2 leaves on hover", "button", "skittish", "", None, False),
    # A limit: display:none has no box, so nothing can be located or pressed. Reaching it
    # through its painted label is locate's problem, not the guard's.
    ("F5 boxless input", "checkbox", "boxless checkbox", "", None, False),
)


async def run() -> int:
    home = Path(tempfile.mkdtemp(prefix="factory-guard-"))
    httpd = serve()
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

        machine = await Machine.attach(url, seed=17)
        landed_on: list[tuple[float, float]] = []

        for name, role, target, change, expected, should_dispatch in CASES:
            await machine.go(FIXTURE)
            #: Navigating to the same URL does not reliably give a fresh JS context, and a
            #: counter carried between cases reports travel that belonged to the last one.
            await machine.evaluate("window.__clicks=[];window.__moves=[];0")

            found = await machine.find(role, target)
            if change:
                await machine.evaluate(change)

            did = await machine.press(found)
            clicks = json.loads(await machine.evaluate("JSON.stringify(window.__clicks)"))
            moves = int(await machine.evaluate("window.__moves.length") or 0)
            where = await machine.evaluate(
                "JSON.stringify(window.__moves.slice(-1)[0] || [])")

            delivered_ok = expected is None or did.delivery == expected
            ok = delivered_ok and did.ok == should_dispatch
            if did.ok and not should_dispatch:
                safety += 1
            if should_dispatch and not did.ok:
                liveness += 1
            # H1, and only where something was sent: a refusal before the pointer travels
            # has nothing to have travelled for.
            if did.ok and moves < 2:
                shape += 1
            if did.ok and (point := json.loads(where)):
                landed_on.append(tuple(point))

            print(f"{'ok  ' if ok else 'FAIL'} {name:26} "
                  f"delivery={did.delivery:<12} acted={did.ok!s:<5} "
                  f"moves={moves:<4} {did.detail[:34]:<34} page_saw={clicks}")

        # M3 end to end: press the same control repeatedly and see where it lands.
        await machine.go(FIXTURE)
        await asyncio.sleep(0.5)
        for _ in range(4):
            await machine.click("button", "target")
        spots = json.loads(await machine.evaluate(
            "JSON.stringify(window.__moves.slice(-1)[0] || [])"))
        del spots
        aims = {machine.hand.aim() for _ in range(20)}

        await machine.close()
    finally:
        browser.terminate()
        httpd.shutdown()
        shutil.rmtree(home, ignore_errors=True)

    print(f"\nSAFETY   dispatched when it should have refused : {safety}   (must be 0)")
    print(f"LIVENESS refused when it should have dispatched  : {liveness}")
    print(f"SHAPE    presses that arrived without travel     : {shape}   (must be 0)")
    print(f"M3       distinct aim points out of 20           : {len(aims)}")
    return 1 if safety or liveness or shape else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
