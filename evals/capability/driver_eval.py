"""Does a candidate walk every gate, and does a refusal say which one?

    uv run python -m evals.capability.driver_eval

No browser and no site. The recording door from `discriminate_eval` stands in for the
BROWSER one, so the whole path runs -- draft, read, publish, install, call, watch -- with
the page replaced by a notebook.

    ADMITTED  something that should not have passed was admitted   must be 0
    MUTE      a refusal did not say which gate                     must be 0
"""

from __future__ import annotations

import ast
import asyncio
import shutil
import sys
import tempfile
from pathlib import Path

from evals.capability.discriminate_eval import PORT, SENT, recording_door
from evals.capability.draft_eval import WORKFLOW, a_run
from factory.capability.amortize import Worth
from factory.capability.driver import Capabilities, Observed, Standing
from factory.core.contract import Contract, Reading
from factory.core.verbs import Doing
from factory.core.workflow import Step, Target, Workflow
from factory.kernel.driver import Door, Kernel
from factory.witness.channel import Channel
from factory.witness.ladder import Ladder


#: A fixture reader on a channel that did not perform the act, so `prove` has something to
#: ask. In an eval a stand-in is a fixture; shipped, it would be product.
class Asked:
    name, channel = "asked", Channel.DESTINATION

    def read(self, did: object, contract: Contract) -> Reading:
        return Reading(values=dict(contract.expects), readable=frozenset(contract.expects))


FILED = Contract(expects={"status": "filed"})


async def run() -> int:
    admitted = mute = failed = 0
    home = Path(tempfile.mkdtemp(prefix="factory-capdriver-"))
    door: asyncio.Task[None] | None = None

    def check(name: str, ok: bool, detail: str) -> None:
        nonlocal failed
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name:50} {detail}")

    try:
        door = asyncio.create_task(recording_door().run_streamable_http_async())
        await asyncio.sleep(2.0)
        wire = Door(name="browser", url=f"http://127.0.0.1:{PORT}/mcp")

        async with await Kernel.start(wire) as kernel:
            gates = Capabilities(kernel, home)

            async def watch(arguments: str) -> Observed:
                """One run, reported two ways: what the door recorded, and what it answered."""
                SENT.clear()
                #: `Cell.result` is the REPR of the trailing expression, so what comes back
                #: is a Python literal and not JSON. Decoding it as JSON fails on the
                #: quoting, which is how this first broke.
                cell = await kernel.run(f"await file_a_note.run({arguments})", timeout=60)
                answered = ast.literal_eval(cell.result) if cell.result else []
                return Observed(sent=list(SENT), returned=answered)

            # G1 -- a candidate with evidence walks the whole path.
            good = await gates.consider(WORKFLOW, a_run(held=True), watch=watch,
                                        contract=FILED, witness=Ladder([Asked()]))
            check("G1 a real candidate is admitted", bool(good), good.line())
            check("G1 and says every gate it passed", len(good.passed) == 7,
                  " -> ".join(good.passed))

            # G1b -- and without a contract it is HELD at prove, never admitted.
            unproven = await gates.consider(WORKFLOW, a_run(held=True), name="unproven",
                                            watch=watch)
            admitted += bool(unproven)
            check("G1 no contract means held at prove",
                  unproven.standing is Standing.HELD and unproven.gate == "prove",
                  unproven.line())

            # G2 -- no evidence, refused at the first gate, and it says so.
            thin = await gates.consider(WORKFLOW, a_run(held=False), watch=watch)
            admitted += bool(thin)
            mute += thin.gate != "draft"
            check("G2 no completed row is refused at draft", not thin and thin.gate == "draft",
                  thin.line())

            # G3 -- a real way for a drafted capability to ignore an argument: the
            # compiler found a parameter varying and no step consumes it. The body then
            # never mentions it, and the reading gate catches that without running it.
            #: Three steps, so `worth` admits it, and a parameter no step consumes -- which
            #: only the reading gate can see. Two steps would be refused as stock first,
            #: and the case would then be testing the wrong gate.
            orphan = Workflow(
                name="orphan-param", params=("note",),
                steps=[s for s in WORKFLOW.steps if s.doing is not Doing.WRITE]
                + [Step(doing=Doing.PRESS, intent="again",
                        target=Target(role="button", name="Save"))])
            deaf = await gates.consider(orphan, a_run(held=True), watch=watch)
            admitted += bool(deaf)
            mute += deaf.gate != "discriminate"
            check("G3 an unconsumed parameter is refused, by reading",
                  not deaf and deaf.gate == "discriminate", deaf.line())

            # G4 -- nothing watching means HELD, never admitted on a static pass.
            unwatched = await gates.consider(WORKFLOW, a_run(held=True), name="unwatched")
            admitted += bool(unwatched)
            check("G4 unobservable is held, not admitted",
                  unwatched.standing is Standing.HELD, unwatched.line())
            check("G4 and it still records what it did pass", "offer" in unwatched.passed,
                  " -> ".join(unwatched.passed))

            # G5 -- THE CALL SITE. The sweep that had none now has one.
            library = [
                Worth(name="pays", authored=1, saved=2.0, uses=5),
                Worth(name="saves-nothing", authored=1, saved=0.0, uses=9),
                Worth(name="brand-new", authored=1, saved=0.0, uses=0),
            ]
            gone = gates.no_longer_offered(library)
            admitted += "pays" in gone or "brand-new" in gone
            check("G5 the driver calls the maintenance sweep", gone == ["saves-nothing"],
                  f"no longer offered: {gone}")
    finally:
        if door is not None:
            door.cancel()
        shutil.rmtree(home, ignore_errors=True)

    print(f"\nADMITTED something that should not have passed : {admitted}   (must be 0)")
    print(f"MUTE     a refusal that did not name its gate   : {mute}   (must be 0)")
    print(f"FAILED   cases not matching                     : {failed}")
    return 1 if admitted or mute or failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
