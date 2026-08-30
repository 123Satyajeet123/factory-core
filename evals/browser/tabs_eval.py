"""Does a demonstration survive the person changing tabs, and does its EVIDENCE?

    uv run python -m evals.browser.tabs_eval

P1 in gates/first-workflow.md, and the prediction I was most confident about: a real
workflow spans surfaces, `session.attach` takes `context.pages[0]`, and nothing in a Step
names a surface. This finds out whether acts on a second tab are recorded at all.

AND THE HALF THAT CARRIES THE PROOF. An act with no evidence beside it can never produce a
contract, so a demonstration that records every act and no traffic compiles to a program
nothing can check. `Bodies` reads request ids off the session that saw them, so a single
collector on the first page loses the same four fifths acts used to. Both are checked here,
because they are one defect in two halves and fixing one reads as fixing both.

THE GAP IS THE EFFECT. `Act.saw` is what the page had fetched WHEN the act happened, so a
response caused by an act lands on the NEXT one. The second press below is what carries the
first press's write, and that ordering is the whole reason `compile/mine.events` needs no
snapshot mechanism.
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
#: TWO PORTS, BECAUSE TWO PAGES ON ONE ORIGIN ARE ONE SURFACE. A first version served both
#: fixtures from one port, `on()` correctly saw it was already there, and the eval blamed
#: the driver for not switching to where it already was.
SITE, OTHER, CDP_PORT = 8087, 8085, 9349


def serve(port: int) -> http.server.ThreadingHTTPServer:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(HERE))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


async def run() -> int:
    home = Path(tempfile.mkdtemp(prefix="factory-tabs-"))
    httpd, elsewhere_httpd = serve(SITE), serve(OTHER)
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
        await second.goto(f"http://127.0.0.1:{OTHER}/form.html")
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
        if not all(a.surface for a in seen):
            faults += 1
            print("FAULT an act was recorded without saying which surface it was on")

        #: RECORDING IS HALF OF IT. A replay has to go back to the surface an act was
        #: demonstrated on, and find it by what it is rather than by where it was.
        from factory.browser import surface as surfaces
        elsewhere = surfaces.of(second.url)
        went = await browser.on(elsewhere)
        did = await browser.click(Target(role="button", name="Save"))
        print(f"\nswitched to {elsewhere}: {went}, then acted: ok={did.ok} "
              f"delivery={did.delivery}")
        if not went or not did.ok:
            faults += 1
            print("FAULT the driver cannot act on a surface it was not started on")

        gone = await browser.on("https://nowhere.invalid")
        print(f"a surface no tab shows: {gone} (must be False)")
        if gone:
            faults += 1
            print("FAULT the driver claimed a surface that is not open")

        #: EVIDENCE, ON THE SURFACE THAT IS NOT THE FIRST. The person's press fetched; the
        #: press after it is the one that carries what the first one caused.
        await asyncio.sleep(0.8)
        elsewhere_acts = [act for act in seen if act.surface == elsewhere]
        carrying = [act for act in elsewhere_acts if act.saw]
        rows = [row for act in elsewhere_acts for e in act.saw for row in e.records()]
        print(f"\nacts on the second surface:        {len(elsewhere_acts)}")
        print(f"  of those, carrying evidence:     {len(carrying)}")
        print(f"  records the evidence parses to:  {len(rows)}")
        for act in elsewhere_acts:
            kinds = ", ".join(e.content_type or "?" for e in act.saw) or "nothing"
            print(f"   {act.doing:<6} saw {len(act.saw)} ({kinds}), among {len(act.among)}")

        if not carrying:
            faults += 1
            print("FAULT a demonstration collects no evidence off the first surface")
        if not rows:
            faults += 1
            print("FAULT evidence was kept but carries no records to derive a contract from")
        if not all(act.among for act in seen):
            faults += 1
            print("FAULT an act was recorded without what else the page was offering")

        await browser.close()
    finally:
        proc.terminate()
        httpd.shutdown()
        elsewhere_httpd.shutdown()
        shutil.rmtree(home, ignore_errors=True)

    print(f"\nFAULTS  surfaces a demonstration would lose : {faults}")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
