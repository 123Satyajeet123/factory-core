"""Does an act, once recorded, resolve back to the same control?

    uv run python -m evals.browser.ledger_eval

A ledger is only worth compiling if what it recorded can be found again. The name a page
reports at record time and the name `locate` searches for at replay time must be the same
name, or every derived workflow misses on its first run.

THIS DRIVES ITSELF, so the acts are the factory's rather than a person's. That is fine for
testing the RECORDER and forbidden for fitting a pace -- see gates/learned-pace.md.
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
from factory.core.ledger import Act, Doing
from factory.core.workflow import Target

HERE = Path(__file__).parent / "fixtures"
SITE, CDP_PORT = 8089, 9347
FIXTURE = f"http://127.0.0.1:{SITE}/guard.html"


def serve() -> http.server.ThreadingHTTPServer:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(HERE))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", SITE), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


async def run() -> int:
    home = Path(tempfile.mkdtemp(prefix="factory-ledger-"))
    httpd = serve()
    browser = profile.launch(home / "profile", CDP_PORT)
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

        driver = await Browser.attach(url, seed=11)
        await driver.go(FIXTURE)
        seen: list[Act] = []
        await driver.watch(seen)

        #: The third leaves the pointer on hover, so the guard refuses and nothing is
        #: dispatched. A ledger records what HAPPENED, not what was attempted -- an act the
        #: page never received is not evidence a person did anything.
        for target in (Target(role="button", name="target"),
                       Target(role="checkbox", name="styled checkbox"),
                       Target(role="button", name="skittish")):
            await driver.click(target)
        await asyncio.sleep(1.0)

        print(f"acts recorded: {len(seen)}")
        for act in seen:
            named = act.target.described() if act.target else "(unresolved)"
            print(f"  {act.doing:<6} {named:<34} value={act.value!r}")

        pressed = [a for a in seen if a.doing is Doing.PRESS and a.target]
        if len(pressed) != 2:
            faults += 1
            print(f"FAULT {len(pressed)} presses reached the page, wanted 2 "
                  "(the third was refused, and a refusal is not an act)")

        #: The property that makes a ledger compilable: what was recorded is findable.
        for act in pressed:
            found = await driver.find(act.target)
            mark = "ok  " if found else "FAIL"
            if not found:
                faults += 1
            print(f"  {mark} recorded {act.target.described():<34} -> {found.why}")

        await driver.close()
    finally:
        browser.terminate()
        httpd.shutdown()
        shutil.rmtree(home, ignore_errors=True)

    print(f"\nFAULTS  acts that cannot be found again : {faults}   (must be 0)")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
