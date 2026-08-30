"""Demonstrate, induce, run, and be told whether it worked.

    uv run python -m evals.browser.vertical_eval

The whole line, on one page, with nothing about that page written down anywhere:

    a person acts        -> browser/record.py  -> a Segment of Acts
    two demonstrations   -> compile/induce.py  -> a Workflow with a parameter
    an observed delta    -> compile/mine.py    -> a Contract binding what CHANGED
    the workflow, rows   -> run/harness.py     -> a Run
    what the page fetched-> witness/           -> a Receipt per step

THE DEMONSTRATIONS ARE DRIVEN BY US, which is fine for testing this line and forbidden for
fitting a pace. The point is whether the pieces connect, not whether a person was involved.
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
import urllib.parse
from pathlib import Path

from factory.browser import profile, record, session
from factory.browser.driver import Browser
from factory.compile.induce import binds_row, induce, workflow_of
from factory.compile.mine import contract_of, mined
from factory.core.ledger import Act, Segment, Whose
from factory.core.workflow import Target
from factory.run import harness
from factory.witness.ladder import Ladder
from factory.witness.readers.fetched import Fetched

HERE = Path(__file__).parent / "fixtures"
SITE, CDP_PORT = 8088, 9348
FIXTURE = f"http://127.0.0.1:{SITE}/form.html"
SAVED: list[dict[str, str]] = []


class Destination(http.server.SimpleHTTPRequestHandler):
    """The system of record. A write goes here and a read comes back from here."""

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/rows.json":
            return super().do_GET()
        asked = urllib.parse.parse_qs(parsed.query).get("name")
        if asked:
            SAVED.append({"id": str(880000 + len(SAVED)), "name": asked[0]})
        body = json.dumps(SAVED).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_: object) -> None:
        return


def serve() -> http.server.ThreadingHTTPServer:
    handler = functools.partial(Destination, directory=str(HERE))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", SITE), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


async def demonstrate(browser: Browser, who: str) -> tuple[Segment, dict]:
    """One demonstration, and the system-of-record delta it caused."""
    await browser.go(FIXTURE)
    seen: list[Act] = []
    await record.acts(browser._at.page, browser.cdp, seen)

    before = list(SAVED)
    name = Target(role="textbox", name="Name")
    found = await browser.find(name)
    await browser.press(found)
    await browser.type(who)
    await browser.click(Target(role="button", name="Save"))
    await asyncio.sleep(1.2)

    return (Segment(whose=Whose.PERSON, intent="add a person", acts=seen),
            {"sor_before": before, "sor_after": list(SAVED)})


async def run() -> int:
    home = Path(tempfile.mkdtemp(prefix="factory-vertical-"))
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

        browser = await Browser.attach(url, seed=23)

        shown, deltas = [], []
        for who in ("Ada Lovelace", "Grace Hopper"):
            segment, delta = await demonstrate(browser, who)
            shown.append(segment)
            deltas.append(delta)
            print(f"demonstrated {who!r}: {len(segment.acts)} acts")

        induced = induce(shown)
        workflow = workflow_of(induced, "add a person")
        print(f"\ninduced      {workflow.name!r} params={workflow.params}")
        for step in workflow.steps:
            print(f"   {step.doing:6} {step.target.described():26} param={step.param!r}")
        if not workflow.params:
            faults += 1
            print("FAULT nothing was found to vary between the demonstrations")

        from openadapt_flow.ir import ActionKind
        from openadapt_flow.ir import Step as TheirStep

        contract = binds_row(contract_of(mined(deltas[-1], TheirStep(
            id="save", intent="add a person", action=ActionKind.CLICK))), workflow, shown)
        print(f"\ncontract     expects={contract.expects} varies={contract.varies} "
              f"identifies={contract.identifies!r}")
        if not contract.varies:
            faults += 1
            print("FAULT the contract still binds the demonstration's own value")
        if not contract.expects:
            faults += 1
            print("FAULT no contract came out of an observed write")
        for step in workflow.steps:
            if step.doing.value == "press" and "Save" in (step.target.name or ""):
                step.contract = contract

        rows = [{"add_a_person": "Alan Turing"}, {"add_a_person": "Katherine Johnson"}]
        was = len(SAVED)
        done = await harness.over(browser, workflow, rows, witness=Ladder((Fetched(),)))

        print(f"\nran {len(done.rows)} rows, destination went from {was} to {len(SAVED)}")
        for row in done.rows:
            marks = " ".join(f"{(s.did.ok and 'ok') or 'no'}" for s in row.steps)
            said = [s.receipt.verdict for s in row.steps if s.receipt]
            print(f"   {row.row} steps=[{marks}] receipts={said}")

        #: THE CHECK THAT NEARLY WAS NOT HERE. Both rows came back CONFIRMED against a
        #: contract holding the demonstration's name, which was true and about neither of
        #: them. A verdict must move when the row's own value is not what landed.
        wrong = contract.for_row({"add_a_person": "Nobody At All"})
        lied = Ladder((Fetched(),)).witness(
            done.rows[0].steps[-1].did, wrong)
        print(f"\ncontrol      a row that wrote nothing of the sort -> {lied.verdict}")
        if lied.verdict.value == "confirmed":
            faults += 1
            print("FAULT the witness confirms a value the run never wrote")

        wrote = [r["name"] for r in SAVED[was:]]
        print(f"\nwritten by the run: {wrote}")
        if wrote != ["Alan Turing", "Katherine Johnson"]:
            faults += 1
            print("FAULT the rows the run was given are not what the destination received")

        await browser.close()
    finally:
        proc.terminate()
        httpd.shutdown()
        shutil.rmtree(home, ignore_errors=True)

    print(f"\nFAULTS  {faults}   (must be 0)")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
