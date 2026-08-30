"""Is the rhythm BETWEEN acts as human as the rhythm inside one?

    uv run python -m evals.browser.rhythm_eval

`gates/human-input.md` covers travel, dwell and the press. This is the gap it did not: what
happens between one act and the next, between one page and the next, and between one row of
work and the next. Measured from the page's own event stream, which is the same channel a
behavioural detector reads.
"""

from __future__ import annotations

import asyncio
import functools
import http.server
import itertools
import shutil
import statistics
import sys
import tempfile
import threading
from pathlib import Path

from factory.browser import profile, session
from factory.browser.driver import Browser
from factory.core.ledger import Act
from factory.core.workflow import Target

HERE = Path(__file__).parent / "fixtures"
SITE, CDP_PORT = 8086, 9350
#: Nothing a hand does arrives faster than this.
FLOOR = 0.10


def serve() -> http.server.ThreadingHTTPServer:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(HERE))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", SITE), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


async def run() -> int:
    home = Path(tempfile.mkdtemp(prefix="factory-rhythm-"))
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

        browser = await Browser.attach(url, seed=41)
        await browser.go(f"http://127.0.0.1:{SITE}/guard.html")
        seen: list[Act] = []
        await browser.watch(seen)

        target = Target(role="button", name="target")
        for _ in range(6):
            await browser.click(target)
        await asyncio.sleep(0.5)
        same_page = [(b.at - a.at).total_seconds()
                     for a, b in itertools.pairwise(seen)]

        before = len(seen)
        await browser.go(f"http://127.0.0.1:{SITE}/guard.html")
        await browser.watch(seen)
        await browser.click(target)
        await asyncio.sleep(0.5)
        after_a_page = ((seen[before].at - seen[before - 1].at).total_seconds()
                        if len(seen) > before else 0.0)

        rows = statistics.median(
            [browser.hand.draw(browser.hand.pace.between_rows) for _ in range(200)])

        print(f"acts on one page      {len(same_page) + 1}")
        print(f"gap between acts      min {min(same_page):.2f}s  "
              f"median {statistics.median(same_page):.2f}s  max {max(same_page):.2f}s")
        print(f"gap after arriving    {after_a_page:.2f}s")
        print(f"gap between rows      {rows:.2f}s (median of the draw)")

        if min(same_page) < FLOOR:
            faults += 1
            print(f"FAULT an act arrived {min(same_page):.3f}s after the last one")
        if len(set(round(g, 3) for g in same_page)) < len(same_page):
            faults += 1
            print("FAULT two gaps are identical, so the rhythm is not drawn")
        if after_a_page <= statistics.median(same_page):
            faults += 1
            print("FAULT arriving somewhere new cost no more than acting again")
        if rows <= statistics.median(same_page):
            faults += 1
            print("FAULT a new row costs no more than the next act in the same one")

        await browser.close()
    finally:
        proc.terminate()
        httpd.shutdown()
        shutil.rmtree(home, ignore_errors=True)

    print(f"\nFAULTS  places the rhythm goes machine-shaped : {faults}   (must be 0)")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
