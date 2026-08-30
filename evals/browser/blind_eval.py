"""What happens on a page that we do not see happening?

    uv run python -m evals.browser.blind_eval

Every other eval asks whether a thing we built works. This one asks what the machinery is
BLIND to -- because a gap here does not announce itself: the ledger looks complete, the run
looks clean, and the missing part left no evidence it was missing.

Not a pass/fail suite. It prints what the page did beside what we recorded, and the
difference is the finding.
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
from factory.core.ledger import Act
from factory.core.workflow import Target

HERE = Path(__file__).parent / "fixtures"
SITE, CDP_PORT = 8083, 9352
FIXTURE = f"http://127.0.0.1:{SITE}/blind.html"


def serve() -> http.server.ThreadingHTTPServer:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(HERE))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", SITE), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


async def run() -> int:
    home = Path(tempfile.mkdtemp(prefix="factory-blind-"))
    httpd = serve()
    proc = profile.launch(home / "profile", CDP_PORT)
    try:
        for _ in range(60):
            try:
                url = session.endpoint(CDP_PORT)
                break
            except OSError:
                await asyncio.sleep(0.25)
        else:
            raise RuntimeError("browser never opened its debugging port")

        browser = await Browser.attach(url, seed=61)
        await browser.go(FIXTURE)
        seen: list[Act] = []
        await browser.watch(seen)

        errors: list[str] = []
        failures: list[str] = []
        dialogs: list[str] = []
        page = browser._at.page
        page.on("pageerror", lambda e: errors.append(str(e)[:40]))
        page.on("requestfailed", lambda r: failures.append(r.url.rsplit("/", 1)[-1]))
        page.on("dialog", lambda d: dialogs.append(d.type))

        #: A person doing ordinary things that are not a click on a button.
        await browser.click(Target(role="button", name="plain"))
        await browser.evaluate("window.scrollTo(0, 600)")
        await browser.evaluate(
            "const s=document.getElementById('pick'); s.value='beta';"
            "s.dispatchEvent(new Event('change',{bubbles:true}))")
        await browser.click(Target(role="button", name="ask something"))
        await browser.click(Target(role="button", name="fetch something missing"))
        await browser.click(Target(role="button", name="throw"))
        await asyncio.sleep(1.5)

        did = json.loads(await browser.evaluate("JSON.stringify(window.__saw)"))
        kinds = sorted({a.doing.value for a in seen})
        exchanges = await browser.fetched()

        print(f"the page saw     : {did}")
        print(f"we recorded      : {len(seen)} acts, kinds {kinds}")
        for act in seen:
            print(f"    {act.doing:<6} {act.target.described() if act.target else '(none)'}")
        print()
        print(f"page errors      : {errors or 'NOT CAPTURED by the driver'}")
        print(f"failed requests  : {failures or 'NOT CAPTURED by the driver'}")
        print(f"dialogs          : {dialogs or 'NOT CAPTURED by the driver'}")
        print(f"exchanges kept   : {len(exchanges)}")

        #: Can we even address something inside a frame?
        inside = await browser.find(Target(role="button", name="inside the frame"))
        print(f"a control inside an iframe: {inside.why}")

        await browser.close()
    finally:
        proc.terminate()
        httpd.shutdown()
        shutil.rmtree(home, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
