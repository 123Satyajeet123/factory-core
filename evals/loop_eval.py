from __future__ import annotations

import ast
import asyncio
import functools
import http.server
import shutil
import socket
import sys
import tempfile
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path

from evals.browser.vertical_eval import HERE, SAVED, Destination, contract_of, mined
from factory.browser import profile, serve, session
from factory.browser.driver import Browser
from factory.capability import notice
from factory.capability.amortize import worth
from factory.capability.driver import Capabilities, Observed, Standing
from factory.capability.publish import importable
from factory.compile.induce import binds_row, induce, workflow_of
from factory.core.ledger import Act, Segment, Whose
from factory.core.workflow import Target
from factory.kernel.driver import Door, Kernel
from factory.observe import Prices, spent
from factory.run import harness
from factory.store import ledger as kept
from factory.witness.ladder import Ladder
from factory.witness.readers.fetched import Fetched

SITE, CDP_PORT = 8096, 9354
TASK = "add a person"


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def site() -> http.server.ThreadingHTTPServer:
    handler = functools.partial(Destination, directory=str(HERE))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", SITE), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


async def demonstrate(browser: Browser, who: str, at: datetime) -> tuple[Segment, dict]:
    await browser.go(f"http://127.0.0.1:{SITE}/form.html")
    seen: list[Act] = []
    await browser.watch(seen)
    before = list(SAVED)
    await browser.press(await browser.find(Target(role="textbox", name="Name")))
    await browser.type(who)
    await browser.click(Target(role="button", name="Save"))
    await asyncio.sleep(1.2)
    dated = [a.model_copy(update={"at": at}) for a in seen]
    return (Segment(whose=Whose.PERSON, intent=TASK, acts=dated),
            {"sor_before": before, "sor_after": list(SAVED)})


async def run() -> int:
    home = Path(tempfile.mkdtemp(prefix="factory-loop-"))
    httpd = site()
    proc = profile.launch(home / "profile", CDP_PORT)
    door_port = free_port()
    broke: list[str] = []
    door = None

    def stage(name: str, ok: bool, detail: str) -> None:
        if not ok:
            broke.append(name)
        print(f"{'ok  ' if ok else 'FAIL'} {name:34} {detail}")

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
        door = asyncio.create_task(serve.serve(browser, door_port))

        when = datetime(2026, 8, 20, 9, 0, tzinfo=UTC)
        shown, deltas = [], []
        for n, who in enumerate(("Ada Lovelace", "Grace Hopper")):
            segment, delta = await demonstrate(browser, who, when + timedelta(days=n))
            kept.keep(segment, TASK, at=home / "ledger")
            shown.append(segment)
            deltas.append(delta)
        stage("1 demonstrated, on two days", len(shown) == 2,
              f"{sum(len(s.acts) for s in shown)} acts kept to the ledger")

        seen = notice.across(TASK, kept.shown(TASK, at=home / "ledger"))
        stage("2 noticed as worth compiling", bool(seen), seen.why())

        workflow = workflow_of(induce(shown), TASK)
        stage("3 induced a parameterised workflow", bool(workflow.params),
              f"{len(workflow.steps)} steps, params={workflow.params}")

        from openadapt_flow.ir import ActionKind
        from openadapt_flow.ir import Step as TheirStep
        contract = binds_row(contract_of(mined(deltas[-1], TheirStep(
            id="save", intent=TASK, action=ActionKind.CLICK))), workflow, shown)
        for step in workflow.steps:
            if step.doing.value == "press" and "Save" in (step.target.name or ""):
                step.contract = contract
        stage("4 mined a contract from the delta", bool(contract.expects),
              f"expects={contract.expects} varies={contract.varies}")

        prices = Prices()
        rows = [{workflow.params[0]: "Alan Turing"}, {workflow.params[0]: "Katherine Johnson"}]
        before_run = await harness.over(browser, workflow, rows,
                                        witness=Ladder((Fetched(),)), prices=prices)
        confirmed = sum(1 for r in before_run.rows for s in r.steps
                        if s.receipt and s.receipt.verdict == "confirmed")
        stage("5 ran it, and a channel that did not act agreed", confirmed > 0,
              f"{len(before_run.rows)} rows, {confirmed} confirmed by the wire")

        module = importable(workflow.name)
        async with await Kernel.start(
                Door(name="browser", url=f"http://127.0.0.1:{door_port}/mcp")) as kernel:

            async def watch(arguments: str) -> Observed:
                cell = await kernel.run(f"await {module}.run({arguments})", timeout=180)
                acts = ast.literal_eval(cell.result) if cell.result else []
                print(f"     watch({arguments}) status={cell.status} {cell.ename}"
                      f" -> {[(a.get('ok'), a.get('value'), a.get('detail')) for a in acts]}")
                return Observed(sent=acts, returned=acts)

            answer = await Capabilities(kernel, home / "skills").consider(
                workflow, before_run, watch=watch, witness=Ladder((Fetched(),)),
                contract=contract, inputs=("'Edsger Dijkstra'", "'Barbara Liskov'"))
            stage("6 walked every gate", answer.standing is not Standing.REFUSED,
                  answer.line())
            stage("6 and passed them in order", len(answer.passed) >= 5,
                  " -> ".join(answer.passed))

            landed = [row["name"] for row in SAVED[-2:]]
            stage("7 a cell's calls reached the destination",
                  "Barbara Liskov" in landed, f"the system of record ends with {landed}")

        after = spent(before_run, prices)
        stage("8 the run priced itself from what it took", after.estimated == 0,
              after.said())

        paid = worth(workflow.name, before_run, [before_run])
        stage("9 and worth is arithmetic, not opinion", paid.uses == 1, paid.line())
    finally:
        if door is not None:
            door.cancel()
        proc.terminate()
        httpd.shutdown()
        shutil.rmtree(home, ignore_errors=True)

    print(f"\nBROKE  stages that did not hold : {len(broke)}   (must be 0)")
    if broke:
        print("       " + ", ".join(broke))
    return 1 if broke else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
