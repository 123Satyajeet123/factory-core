"""Can anything reach the page through the door without being guarded?

    uv run python -m evals.browser.door_eval

The door is what a KERNEL cell -- model-written code in another interpreter -- uses to act.
If a caller can get an unguarded press through it, every guarantee the BROWSER driver
makes is optional, and optional guarantees are not guarantees.

Also answers the open item in gates/kernel-browser-wire.md: what one act costs over the
wire.
"""

from __future__ import annotations

import asyncio
import functools
import http.server
import shutil
import statistics
import tempfile
import threading
import time
from pathlib import Path

from factory.browser import profile, serve, session
from factory.browser.driver import Browser

HERE = Path(__file__).parent / "fixtures"
SITE, CDP_PORT, DOOR = 8090, 9346, 8765
FIXTURE = f"http://127.0.0.1:{SITE}/guard.html"

#: A tool taking any of these would hand a caller a way past the guard.
UNGUARDED = ("coordinate", "selector", "xpath", "x", "y", "backend_node_id", "cdp")


def site() -> http.server.ThreadingHTTPServer:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(HERE))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", SITE), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


async def run() -> int:
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    home = Path(tempfile.mkdtemp(prefix="factory-door-"))
    httpd = site()
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

        driver = await Browser.attach(url, seed=5)
        await driver.go(FIXTURE)
        door = asyncio.create_task(serve.serve(driver, DOOR))
        await asyncio.sleep(2.0)

        async with (streamablehttp_client(f"http://127.0.0.1:{DOOR}/mcp") as (r, w, _),
                    ClientSession(r, w) as client):
            if True:
                await client.initialize()
                tools = (await client.list_tools()).tools
                names = sorted(t.name for t in tools)
                print(f"door offers        {names}")

                for tool in tools:
                    args = set((tool.inputSchema or {}).get("properties", {}))
                    leaks = args & set(UNGUARDED)
                    if leaks:
                        faults += 1
                        print(f"FAULT {tool.name} takes {leaks} -- a way past the guard")

                async def call(tool: str, **args: object) -> object:
                    """Whatever the tool returned, in its own shape.

                    FastMCP puts a typed return in `structuredContent`; the text parts are
                    a rendering of it. Reading the first text part as JSON works for a dict
                    and fails for a list of strings, which is how this eval first broke.
                    """
                    got = await client.call_tool(tool, args)
                    if got.structuredContent is not None:
                        inner = got.structuredContent
                        return inner.get("result", inner) if isinstance(inner, dict) else inner
                    return [c.text for c in got.content]

                print(f"candidates         {await call('candidates')}")

                #: THE WIRE, ISOLATED. A click costs mostly travel and rest -- our own
                #: pacing -- so timing one says nothing about transport. The same read done
                #: through the door and directly differ by exactly the wire.
                over, direct = [], []
                for _ in range(5):
                    started = time.perf_counter()
                    await call("candidates")
                    over.append(time.perf_counter() - started)
                    started = time.perf_counter()
                    await driver.candidates()
                    direct.append(time.perf_counter() - started)
                wire = statistics.median(over) - statistics.median(direct)
                print(f"same read: door {statistics.median(over) * 1000:.0f} ms, "
                      f"direct {statistics.median(direct) * 1000:.0f} ms, "
                      f"wire {wire * 1000:.0f} ms")

                timings = []
                for _ in range(3):
                    started = time.perf_counter()
                    did = await call("click", role="button", name="target")
                    timings.append(time.perf_counter() - started)
                print(f"click through door ok={did['ok']} delivery={did['delivery']} "
                      f"detail={did['detail']}")
                print(f"one guarded act    {statistics.median(timings) * 1000:.0f} ms "
                      f"(travel and rest, not transport)")
                if not did["ok"]:
                    faults += 1
                    print("FAULT a plain press should have landed")

                #: The world changes under the caller. The door must refuse exactly as the
                #: driver does -- this is the whole reason the door exists.
                await driver.evaluate("document.getElementById('veil').style.display='block'")
                covered = await call("click", role="button", name="target")
                print(f"covered target     ok={covered['ok']} "
                      f"delivery={covered['delivery']} detail={covered['detail']}")
                if covered["ok"]:
                    faults += 1
                    print("FAULT the door pressed through an overlay")



        door.cancel()
        await driver.close()
    finally:
        browser.terminate()
        httpd.shutdown()
        shutil.rmtree(home, ignore_errors=True)

    print(f"\nFAULTS  ways past the guard, or guarded acts that failed : {faults}   (must be 0)")
    return 1 if faults else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
