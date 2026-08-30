"""Does the recorder see what the page sees, and does a fit form from it?

    uv run python -m evals.browser.record_eval

THIS TESTS THE RECORDER, NOT A FIT. The events below are produced by our own hand, and
`gates/learned-pace.md` forbids fitting to the factory's own driving: the distribution
would converge on whatever we already do. What is being checked is that the listeners see
a real event stream at all, and that `fit` forms parameters from it and says which it
could not.
"""

from __future__ import annotations

import asyncio
import functools
import http.server
import shutil
import tempfile
import threading
from pathlib import Path

from factory.browser import pace as pace_mod
from factory.browser import profile, record, session
from factory.browser.driver import Browser
from factory.core.workflow import Target

HERE = Path(__file__).parent / "fixtures"
PORT, CDP_PORT = 8091, 9345


def serve() -> http.server.ThreadingHTTPServer:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(HERE))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


async def run() -> int:
    home = Path(tempfile.mkdtemp(prefix="factory-record-"))
    httpd = serve()
    browser = profile.launch(home / "profile", CDP_PORT)
    try:
        for _ in range(60):
            try:
                url = session.endpoint(CDP_PORT)
                break
            except OSError:
                await asyncio.sleep(0.25)
        else:
            raise RuntimeError("browser never opened its debugging port")

        driver = await Browser.attach(url, seed=3)
        await driver.go(f"http://127.0.0.1:{PORT}/guard.html")
        await record.watch(driver._at.page)

        for _ in range(6):
            await driver.click(Target(role="button", name="target"))
        await driver.type("abcdefghij")

        watched = await record.drain(driver._at.page)
        print(f"recorder saw   moves={len(watched.moves)}  keys={len(watched.keys)}  "
              f"presses={len(watched.presses)}  releases={len(watched.releases)}")

        landed = [(fx, fy) for _, fx, fy in watched.presses if fx is not None]
        print(f"landing points {len(set(landed))} distinct of {len(landed)}")

        fitted = pace_mod.fit(watched)
        print(f"fit samples    {fitted.samples}")
        print(f"kept default   {fitted.kept_default or '(none)'}")
        print(f"keystroke      default {pace_mod.Pace().keystroke} "
              f"-> fitted {tuple(round(v, 3) for v in fitted.pace.keystroke)}")

        await driver.close()
    finally:
        browser.terminate()
        httpd.shutdown()
        shutil.rmtree(home, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
