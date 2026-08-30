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

from factory.browser import bodies as bodies_mod
from factory.browser import locate, profile, session

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
        for _ in range(40):
            try:
                url = session.endpoint(CDP_PORT)
                break
            except OSError:
                await asyncio.sleep(0.25)
        else:
            raise RuntimeError("browser never opened its debugging port")

        live = await session.attach(url)
        cdp = await live.get_or_create_cdp_session()
        watcher = bodies_mod.Bodies()
        await cdp.cdp_client.send.Network.enable(session_id=cdp.session_id)
        watcher.watch(cdp.cdp_client)

        print(f"{'surface':10} {'DOM: interactive / named':28} {'WIRE: bodies kept':20}")
        print("-" * 62)
        for surface in ("dom", "wire", "painted"):
            watcher.exchanges.clear()
            await cdp.cdp_client.send.Page.navigate(
                params={"url": f"http://127.0.0.1:{PORT}/{surface}.html"},
                session_id=cdp.session_id)
            await asyncio.sleep(1.2)

            nodes = await locate.visible(live)
            named = [n for n in nodes.values() if (getattr(n.ax_node, "name", "") or "").strip()]
            kept = await watcher.drain(cdp.cdp_client, cdp.session_id)
            bodies_seen = [e for e in kept if e.body]

            print(f"{surface:10} {f'{len(nodes)} / {len(named)}':28} "
                  f"{f'{len(bodies_seen)} of {len(kept)} responses':20}")
            for e in kept:
                print(f"{'':10} saw  {e.status} ct={e.content_type.split(';')[0]!r:22} "
                      f"size={e.size} body={'yes' if e.body else 'no'} {e.url[-28:]}")
            for e in bodies_seen:
                print(f"{'':10} kept {e.status} {e.content_type.split(';')[0]:18} "
                      f"{e.size:>6}B  {(e.body or '')[:60]!r}")

        await live.stop()
    finally:
        browser.terminate()
        httpd.shutdown()
        shutil.rmtree(home, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
