"""What can this machinery SEE, on surfaces of different kinds?

    uv run python -m evals.browser.perceive_eval

Not a workflow and not a site. Three kinds of surface, which is a taxonomy of how pages
carry their data rather than of who serves them:

    DOM       the values are in the document, with accessible roles and names
    WIRE      the document holds nothing; the values arrive as JSON the page fetched
    PAINTED   the values are drawn to a canvas and exist in neither

Both channels are asked about all three, and what neither can see is the finding.
"""

from __future__ import annotations

import asyncio
import functools
import http.server
import shutil
import tempfile
import threading
from pathlib import Path

from factory.browser import profile, session
from factory.browser.machine import Machine

HERE = Path(__file__).parent / "fixtures"
PORT, CDP_PORT = 8099, 9334


def serve(root: Path) -> http.server.ThreadingHTTPServer:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


async def run() -> int:
    home = Path(tempfile.mkdtemp(prefix="factory-perceive-"))
    httpd = serve(HERE)
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

        machine = await Machine.attach(url)
        print(f"{'surface':10} {'accessible: nodes / named':28} {'wire: bodies kept':20}")
        print("-" * 62)
        for surface in ("dom", "wire", "painted"):
            machine.bodies.exchanges.clear()
            await machine.go(f"http://127.0.0.1:{PORT}/{surface}.html")
            await asyncio.sleep(0.8)

            nodes = await machine.candidates()
            named = [n for n in nodes if (n.get("name") or {}).get("value")]
            kept = await machine.fetched()
            with_body = [e for e in kept if e.body]

            print(f"{surface:10} {f'{len(nodes)} / {len(named)}':28} "
                  f"{f'{len(with_body)} of {len(kept)} responses':20}")
            for exchange in with_body:
                print(f"{'':10} kept {exchange.status} {exchange.content_type:18} "
                      f"{exchange.size:>6}B  {(exchange.body or '')[:52]!r}")

        await machine.close()
    finally:
        browser.terminate()
        httpd.shutdown()
        shutil.rmtree(home, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
