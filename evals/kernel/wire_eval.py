"""Can a cell act on a page, and is the act guarded because of where it came from?

    uv run python -m evals.kernel.wire_eval

The whole wire, end to end: a cell in its own interpreter -> `rlm.mcp` -> the door in
`browser/serve.py` -> the guard -> a real page. This is the claim
gates/kernel-browser-wire.md settled by reading two vendors, executed for the first time.

    ESCAPED   a cell reached something the host did not declare    must be 0
    UNGUARDED a cell's act bypassed the guard                      must be 0
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

from factory.browser import profile, serve, session
from factory.browser.driver import Browser
from factory.kernel.driver import Door, Kernel

HERE = Path(__file__).resolve().parents[1] / "browser" / "fixtures"
SITE, CDP_PORT, DOOR = 8091, 9347, 8766
FIXTURE = f"http://127.0.0.1:{SITE}/guard.html"


def site() -> http.server.ThreadingHTTPServer:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(HERE))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", SITE), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


async def run() -> int:
    home = Path(tempfile.mkdtemp(prefix="factory-wire-"))
    httpd = site()
    browser = profile.launch(home / "profile", CDP_PORT)
    escaped = unguarded = failed = 0

    def check(name: str, ok: bool, detail: str) -> None:
        nonlocal failed
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name:38} {detail}")

    try:
        for _ in range(60):
            try:
                cdp = session.endpoint(CDP_PORT)
                break
            except OSError:
                await asyncio.sleep(0.25)
        else:
            raise RuntimeError("browser never opened its debugging port")

        driver = await Browser.attach(cdp, seed=5)
        await driver.go(FIXTURE)
        door = asyncio.create_task(serve.serve(driver, DOOR))
        await asyncio.sleep(2.0)

        wire = Door(name="browser", url=f"http://127.0.0.1:{DOOR}/mcp")
        async with await Kernel.start(wire) as wired:
            cell = await wired.run("import rlm.mcp as mcp", timeout=30)
            check("W1 a cell can import the client", cell.status == "ok", cell.ename or "ok")

            cell = await wired.run('sorted(t["name"] for t in await mcp.list_tools("browser"))',
                                   timeout=30)
            offered = cell.result or ""
            check("W2 the door answers a cell", "click" in offered, offered[:60])

            cell = await wired.run(
                'await mcp.call_tool("browser", "click", {"role": "button", "name": "target"})',
                timeout=60)
            acted = "target_hit" in (cell.result or "")
            check("W3 a cell acts on the page", acted, (cell.result or cell.evalue)[:60])

            saw = json.loads(await driver.evaluate("JSON.stringify(window.__clicks || [])"))
            check("W3 the page received it", "target" in saw, f"page saw {saw}")

            # W4 -- the guard applies to a cell exactly as to any other caller.
            await driver.evaluate("document.getElementById('veil').style.display='block'")
            cell = await wired.run(
                'await mcp.call_tool("browser", "click", {"role": "button", "name": "target"})',
                timeout=60)
            refused = "intercepted" in (cell.result or "")
            unguarded += not refused
            check("W4 the guard refuses a cell's act", refused, (cell.result or "")[:60])

            before = json.loads(await driver.evaluate("JSON.stringify(window.__clicks || [])"))
            check("W4 and nothing was dispatched", before == saw, f"page saw {before}")

            # W5 -- a server the host never declared stays unreachable.
            cell = await wired.run('await mcp.list_tools("anything-else")', timeout=30)
            reached = cell.status == "ok"
            escaped += reached
            check("W5 an undeclared server is refused", not reached,
                  cell.ename or "REACHED IT")

        door.cancel()
    finally:
        browser.terminate()
        httpd.shutdown()
        shutil.rmtree(home, ignore_errors=True)

    print(f"\nESCAPED   reached something undeclared : {escaped}   (must be 0)")
    print(f"UNGUARDED an act bypassed the guard    : {unguarded}   (must be 0)")
    print(f"FAILED    cases not matching           : {failed}")
    return 1 if escaped or unguarded or failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
