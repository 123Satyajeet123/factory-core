"""The guard's fixtures and the shape of the input, driven through the driver.

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
from factory.browser.driver import Browser
from factory.core.evidence import Delivery
from factory.core.workflow import Target


def picks(described: str):
    """A stand-in for the model rung.

    Deliberately dumb: it matches the candidate descriptions the driver offers, which is the
    same input a model would get. It knows no selector and no id, so a rung that only passed
    because this helper cheats would be visible.

    Matching a whole description rather than a fragment, because the accessibility tree
    carries StaticText children -- `button 'target'` and `statictext 'target'` both contain
    the name, and a substring match found two and refused.
    """
    async def chooser(wanted: str, among: dict[int, str]) -> int | None:
        hits = [i for i, line in among.items() if line == described]
        return hits[0] if len(hits) == 1 else None
    return chooser

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

#: name, target, chooser, change applied after finding, expected delivery, dispatch, rung.
#: A `None` delivery means any refusal will do -- the claim is that nothing was sent.
CASES = (
    ("F1 impostor swap", Target(role="button", name="target"), None,
     "const n=document.createElement('button');n.id='target';"
     "document.getElementById('target').replaceWith(n);",
     Delivery.OFF_TARGET, False, "structural"),
    ("F2 consent overlay", Target(role="button", name="target"), None,
     "document.getElementById('veil').style.display='block';",
     Delivery.INTERCEPTED, False, "structural"),
    ("F3 label for hidden input", Target(role="checkbox", name="styled checkbox"),
     None, "", Delivery.TARGET_HIT, True, "accessible"),
    ("F4 target off viewport", Target(role="button", name="target"), None,
     "document.getElementById('target').style.position='fixed';"
     "document.getElementById('target').style.top='-500px';",
     Delivery.OFF_TARGET, False, "structural"),
    ("H2 leaves on hover", Target(role="button", name="skittish"), None,
     "", None, False, "structural"),
    # A limit: display:none has no box, so nothing can be located or pressed. Reaching it
    # through its painted label is locate's problem, not the guard's.
    ("F5 boxless input", Target(role="checkbox", name="boxless checkbox"), None,
     "", None, False, "structural"),
    # L6: rung 0 refuses two matches rather than taking the first, and the chooser -- given
    # only the descriptions the driver offers -- settles it. This is also the only case in
    # the suite that is expected to actually press something.
    ("L1 ambiguity, chooser settles", Target(role="button"), picks("button 'target'"),
     "", Delivery.TARGET_HIT, True, "chosen"),
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

        driver = await Browser.attach(url, seed=17)
        landed_on: list[tuple[float, float]] = []

        questions = 0
        for name, target, chooser, change, expected, should_dispatch, want_rung in CASES:
            await driver.go(FIXTURE)
            #: Navigating to the same URL does not reliably give a fresh JS context, and a
            #: counter carried between cases reports travel that belonged to the last one.
            await driver.evaluate("window.__clicks=[];window.__moves=[];0")

            found = await driver.find(target, chooser)
            if found.question:
                questions += 1
            if change:
                await driver.evaluate(change)

            did = await driver.press(found)
            clicks = json.loads(await driver.evaluate("JSON.stringify(window.__clicks)"))
            moves = int(await driver.evaluate("window.__moves.length") or 0)
            where = await driver.evaluate(
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

            print(f"{'ok  ' if ok else 'FAIL'} {name:30} rung={found.rung:<11} "
                  f"delivery={did.delivery:<12} acted={did.ok!s:<5} "
                  f"moves={moves:<4} {did.detail[:30]:<30} saw={clicks}")
            del want_rung

        # M3 end to end: press the same control repeatedly and see where it lands.
        await driver.go(FIXTURE)
        await asyncio.sleep(0.5)
        for _ in range(4):
            await driver.click(Target(role="button", name="target"))
        spots = json.loads(await driver.evaluate(
            "JSON.stringify(window.__moves.slice(-1)[0] || [])"))
        del spots
        aims = {driver.hand.aim() for _ in range(20)}

        await driver.close()
    finally:
        browser.terminate()
        httpd.shutdown()
        shutil.rmtree(home, ignore_errors=True)

    print(f"\nSAFETY   dispatched when it should have refused : {safety}   (must be 0)")
    print(f"LIVENESS refused when it should have dispatched  : {liveness}")
    print(f"SHAPE    presses that arrived without travel     : {shape}   (must be 0)")
    print(f"M3       distinct aim points out of 20           : {len(aims)}")
    print(f"L6       refusals that produced a question       : {questions}")
    return 1 if safety or liveness or shape else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
