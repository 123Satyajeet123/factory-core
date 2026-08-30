"""Does the second run cost less than the first, for the same result?

    uv run python -m evals.browser.cheaper_eval

gates/cheaper-over-runs.md. The chooser stands in for a model and COUNTS being consulted, so
"cheaper" is measured where the cost is rather than inferred from a clock.
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
from factory.core.memory import Kind
from factory.core.verbs import Doing
from factory.core.workflow import Step, Target
from factory.memory.driver import Memory
from factory.run import select

HERE = Path(__file__).parent / "fixtures"
SITE, CDP_PORT = 8084, 9351
FIXTURE = f"http://127.0.0.1:{SITE}/guard.html"

#: Ambiguous on purpose: two buttons, so rung 0 refuses and something must choose.
STEP = Step(doing=Doing.PRESS, intent="press the one that matters",
            target=Target(role="button"))


class Counting:
    """A model that is not here. It counts being needed."""

    def __init__(self, described: str) -> None:
        self.described, self.asked = described, 0

    async def __call__(self, _wanted: str, among: dict[int, str]) -> int | None:
        self.asked += 1
        hits = [i for i, line in among.items() if line == self.described]
        return hits[0] if len(hits) == 1 else None


def serve() -> http.server.ThreadingHTTPServer:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(HERE))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", SITE), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


async def run() -> int:
    home = Path(tempfile.mkdtemp(prefix="factory-cheaper-"))
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

        browser = await Browser.attach(url, seed=53)
        memory = Memory()
        chooser = Counting("button 'target'")

        await browser.go(FIXTURE)
        first = await select.target_for(browser, STEP, chooser=chooser,
                                        memory=memory, workflow="w", run="r1")
        print(f"run 1   rung={first.rung:<11} asked={chooser.asked}  {first.why}")

        await browser.go(FIXTURE)
        second = await select.target_for(browser, STEP, chooser=chooser,
                                         memory=memory, workflow="w", run="r1")
        print(f"run 2   rung={second.rung:<11} asked={chooser.asked}  {second.why}")

        if first.rung != "chosen" or second.rung != "remembered":
            faults += 1
            print("FAULT the second run did not take a cheaper path than the first")
        if chooser.asked != 1:
            faults += 1
            print(f"FAULT the model was consulted {chooser.asked} times for two runs")

        kept = memory.recall(Kind.TARGET, select.asked_about(STEP, "w"), run="r1")
        print(f"kept    {kept.value if kept else None} at {kept.tier if kept else '-'}")
        if not kept or kept.value.get("name") != "target":
            faults += 1
            print("FAULT what was remembered is not a target that can be searched for")

        #: R3, and the one I predicted would be wrong. The page moves on.
        await browser.go(FIXTURE)
        await browser.evaluate(
            "document.getElementById('target').textContent = 'renamed'")
        again = Counting("button 'renamed'")
        stale = await select.target_for(browser, STEP, chooser=again,
                                        memory=memory, workflow="w", run="r1")
        print(f"moved on rung={stale.rung:<10} asked={again.asked}  {stale.why}")
        if not stale or stale.rung != "chosen":
            faults += 1
            print("FAULT a remembered target that no longer resolves did not descend again")

        #: R5. A chooser that declines leaves nothing behind.
        empty = Memory()
        declines = Counting("nothing of the sort")
        got = await select.target_for(browser, STEP, chooser=declines,
                                      memory=empty, workflow="w", run="r2")
        left = empty.recall(Kind.TARGET, select.asked_about(STEP, "w"), run="r2")
        print(f"declined rung={got.rung:<10} remembered={left is not None} (must be False)")
        if left is not None:
            faults += 1
            print("FAULT a refusal was remembered as an answer")

        #: THE BOTTOM RUNG. Rung 0 refuses, the model declines, and a person is asked --
        #: once. What they said is kept exactly as a model's answer would be, so the run
        #: after this one costs nothing.
        class Answers:
            def __init__(self, said: str) -> None:
                self.said, self.asked = said, 0

            def ask(self, question: object) -> str:
                self.asked += 1
                return self.said

        forgetful = Memory()
        declines = Counting("nothing matches this")
        person = Answers("button 'target'")
        await browser.go(FIXTURE)
        asked = await select.target_for(browser, STEP, chooser=declines, authority=person,
                                        memory=forgetful, workflow="w", run="r3")
        print(f"asked   rung={asked.rung:<11} person={person.asked}  {asked.why}")

        await browser.go(FIXTURE)
        after = await select.target_for(browser, STEP, chooser=declines, authority=person,
                                        memory=forgetful, workflow="w", run="r3")
        print(f"after   rung={after.rung:<11} person={person.asked}  {after.why}")

        if asked.rung != "asked" or not asked:
            faults += 1
            print("FAULT nobody was asked when neither rung could resolve it")
        if after.rung != "remembered" or person.asked != 1:
            faults += 1
            print(f"FAULT a person was asked {person.asked} times for two runs")

        await browser.close()
    finally:
        proc.terminate()
        httpd.shutdown()
        shutil.rmtree(home, ignore_errors=True)

    print(f"\nFAULTS  {faults}   (must be 0)")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
