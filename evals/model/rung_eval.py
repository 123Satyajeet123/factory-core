"""Does the expensive rung actually make the next run free?

    uv run --with python-dotenv python -m evals.model.rung_eval

NEEDS A CREDENTIAL, AND SPENDS ONE CALL. The whole claim of the ladder in one measurement: a
model resolves an ambiguity once, what it decided is kept as a role and a name, and the run
after costs nothing. Every other eval of this uses a stub chooser; this is the rung with a
model actually in it.
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

from dotenv import load_dotenv

from factory.browser import profile, session
from factory.browser.driver import Browser
from factory.core.memory import Kind
from factory.core.verbs import Doing
from factory.core.workflow import Step, Target
from factory.memory.driver import Memory
from factory.model.driver import MODELS, chooser
from factory.run import select

HERE = Path(__file__).parents[1] / "browser" / "fixtures"
SITE, CDP_PORT = 8080, 9355
#: Ambiguous on purpose: the fixture has two buttons, so rung 0 refuses.
STEP = Step(doing=Doing.PRESS, intent="press the control that is the target",
            target=Target(role="button"))


def serve() -> http.server.ThreadingHTTPServer:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(HERE))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", SITE), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


async def run() -> int:
    load_dotenv(".env")
    choosing = chooser()
    if choosing is None:
        print("no credential: the rung is absent and ambiguity becomes a question.")
        return 0

    counted = {"asked": 0}

    async def watched(wanted: str, among: dict[int, str]) -> int | None:
        counted["asked"] += 1
        return await choosing(wanted, among)

    home = Path(tempfile.mkdtemp(prefix="factory-rung-"))
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

        browser = await Browser.attach(url, seed=83)
        memory = Memory()
        page = f"http://127.0.0.1:{SITE}/guard.html"

        #: A FREE MODEL SOMETIMES REFUSES THE SAME QUESTION IT ANSWERED. Measured: asked
        #: twice about one page, it said "none of these" once and chose correctly once.
        #: Refusing is the safe direction -- it falls to a person -- so the property under
        #: test is not "it always chooses" but "once it has, nobody is asked again".
        chose = None
        for attempt in range(3):
            await browser.go(page)
            chose = await select.target_for(browser, STEP, chooser=watched, memory=memory,
                                            workflow="w", run="r1")
            print(f"try {attempt + 1}   rung={chose.rung:<12} "
                  f"model asked={counted['asked']}  {chose.why}")
            if chose.rung == "chosen":
                break

        spent = counted["asked"]
        await browser.go(page)
        again = await select.target_for(browser, STEP, chooser=watched, memory=memory,
                                        workflow="w", run="r1")
        print(f"after   rung={again.rung:<12} model asked={counted['asked']}  {again.why}")
        first = chose

        kept = memory.recall(Kind.TARGET, select.asked_about(STEP, "w"), run="r1")
        print(f"kept    {kept.value if kept else None}")
        print(f"model   {MODELS[0]}")

        if first.rung != "chosen":
            faults += 1
            print("FAULT three asks and the model never resolved it")
        if again.rung != "remembered":
            faults += 1
            print("FAULT the run after a resolution did not take the free path")
        if counted["asked"] != spent:
            faults += 1
            print(f"FAULT the model was asked again after answering ({counted['asked']})")

        await browser.close()
    finally:
        proc.terminate()
        httpd.shutdown()
        shutil.rmtree(home, ignore_errors=True)

    print(f"\nFAULTS  {faults}   (must be 0)")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
