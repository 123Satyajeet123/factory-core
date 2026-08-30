"""Does a demonstration survive the person changing tabs?

    uv run python -m evals.browser.tabs_eval

P1 in gates/first-workflow.md, and the prediction I was most confident about: a real
workflow spans surfaces, `session.attach` takes `context.pages[0]`, and nothing in a Step
names a surface. This finds out whether acts on a second tab are recorded at all.
"""

from __future__ import annotations

import asyncio
import functools
import http.server
import shutil
import sys
import tempfile
import threading
from pathlib import Path

from factory.browser import profile, session
from factory.browser.driver import Browser
from factory.core.ledger import Act

HERE = Path(__file__).parent / "fixtures"
SITE, CDP_PORT = 8087, 9349


def serve() -> http.server.ThreadingHTTPServer:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(HERE))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", SITE), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


async def run() -> int:
    home = Path(tempfile.mkdtemp(prefix="factory-tabs-"))
    httpd = serve()
    proc = profile.launch(home / "profile", CDP_PORT)
    faults = 0
    try:
        for _ in range(60):
            try:
                url = session.endpoint(CDP_PORT)
                break
            except OSError:
                await asyncio.sleep(0.25)
        else:
            raise RuntimeError("browser never opened its debugging port")

        browser = await Browser.attach(url, seed=31)
        await browser.go(f"http://127.0.0.1:{SITE}/guard.html")
        seen: list[Act] = []
        await browser.watch(seen)

        context = browser._at.context
        print(f"pages the driver knows about: {len(context.pages)}")

        #: A person opening a second surface, the way five tabs happen.
        second = await context.new_page()
        await second.goto(f"http://127.0.0.1:{SITE}/form.html")
        await asyncio.sleep(0.6)
        print(f"after the person opens one:   {len(context.pages)}")

        #: An act on the FIRST surface, through the driver.
        from factory.core.workflow import Target
        await browser.click(Target(role="button", name="target"))
        await asyncio.sleep(0.5)
        on_first = len(seen)

        #: An act on the SECOND, performed in the page itself -- which is what a person
        #: does. Nothing about it goes through our driver.
        await second.click("#save")
        await asyncio.sleep(0.8)
        on_second = len(seen) - on_first

        print(f"acts recorded on the first surface:  {on_first}")
        print(f"acts recorded on the second surface: {on_second}")
        for act in seen:
            named = act.target.described() if act.target else "(unresolved)"
            print(f"   {act.doing:<6} {named}")

        if on_second == 0:
            faults += 1
            print("\nFAULT acts on a second surface are not recorded at all")
        if len(context.pages) > 1 and browser._at.page is context.pages[0]:
            print("      and the driver is still bound to the first page it was given")

        await browser.close()
    finally:
        proc.terminate()
        httpd.shutdown()
        shutil.rmtree(home, ignore_errors=True)

    print(f"\nFAULTS  surfaces a demonstration would lose : {faults}")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
