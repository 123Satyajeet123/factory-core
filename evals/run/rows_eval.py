"""Where does a workflow get its rows, and what does it do when it cannot?

    uv run python -m evals.run.rows_eval

gates/where-rows-come-from.md. Three destinations, none of them named in any driver: one
that sends records, one that paints them, and one whose records do not carry what the
workflow asked for.
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
from factory.core.workflow import Source, Workflow
from factory.run import rows

HERE = Path(__file__).parents[1] / "browser" / "fixtures"
SITE, CDP_PORT = 8081, 9354


def serve() -> http.server.ThreadingHTTPServer:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(HERE))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", SITE), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def flow(source: Source | None) -> Workflow:
    return Workflow(name="outreach", params=("who",), source=source)


async def run() -> int:
    home = Path(tempfile.mkdtemp(prefix="factory-rows-"))
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

        browser = await Browser.attach(url, seed=71)
        here = f"http://127.0.0.1:{SITE}"

        #: S3. Nobody has said where the rows come from.
        got = await rows.of(browser, flow(None))
        print(f"no source        rows={len(got.rows)} asks={got.question.because!r}")
        if got:
            faults += 1
            print("FAULT a workflow with no source ran anyway")

        #: The ordinary case: a destination that sends its records.
        await browser.go(f"{here}/wire.html")
        await asyncio.sleep(0.8)
        got = await rows.of(browser, flow(Source(surface=here, feeds={"name": "who"})))
        print(f"sends records    rows={len(got.rows)} {got.rows[:2]}")
        if not got or len(got.rows) != 2:
            faults += 1
            print("FAULT a destination that sends records yielded none")

        #: S3 again, and my blind prediction: a surface that paints has no source either.
        await browser.go(f"{here}/painted.html")
        await asyncio.sleep(0.8)
        got = await rows.of(browser, flow(Source(surface=here, feeds={"name": "who"})))
        asks = got.question.because if got.question else None
        offered = got.question.candidates if got.question else ()
        print(f"paints them      rows={len(got.rows)} asks={asks!r} offered={offered}")
        if got:
            faults += 1
            print("FAULT a painted surface was read as a source")

        #: S4. The records are there and do not carry what was asked for.
        await browser.go(f"{here}/wire.html")
        await asyncio.sleep(0.8)
        got = await rows.of(browser, flow(Source(surface=here, feeds={"phone": "who"})))
        asks = got.question.because if got.question else ""
        offered = got.question.candidates if got.question else ()
        print(f"wrong field      rows={len(got.rows)} asks={asks!r} offered={offered}")
        if got or "phone" not in asks:
            faults += 1
            print("FAULT a mapping that cannot be satisfied did not say which field")

        await browser.close()
    finally:
        proc.terminate()
        httpd.shutdown()
        shutil.rmtree(home, ignore_errors=True)

    print(f"\nFAULTS  runs that would have gone ahead regardless : {faults}   (must be 0)")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
