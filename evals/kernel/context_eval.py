"""What does holding an object in the kernel actually save?

    uv run python -m evals.kernel.context_eval

No browser and no site. The object is the shape this system really has -- a run of rows
with exchanges attached -- and the claim is a ratio: what it would have cost in a context
window against what the model is actually told.

    LEAKED   the handle is not smaller than the object   must be 0
    BLIND    a cell could not answer from the object     must be 0
"""

from __future__ import annotations

import asyncio
import json
import sys

from factory.kernel.context import place
from factory.kernel.driver import Kernel

#: 800 rows with a nested exchange each: a small run by this system's standards, and
#: already far past what belongs in a prompt.
RUN = [
    {"row": n, "status": "approved" if n % 7 else "held", "owner": f"person-{n % 23}",
     "exchange": {"url": f"/api/records/{n}", "status": 200,
                  "body": {"id": n, "note": "x" * 60}}}
    for n in range(800)
]


async def run() -> int:
    leaked = blind = failed = 0

    def check(name: str, ok: bool, detail: str) -> None:
        nonlocal failed
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name:40} {detail}")

    async with await Kernel.start() as kernel:
        handle = await place(kernel, "run_rows", RUN)

        print(f"\nthe handle a model is given:\n  {handle.prompt()}\n")
        smaller = handle.shown < handle.saved
        leaked += not smaller
        check("C1 the handle is smaller than the object", smaller,
              f"{handle.saved:,} B object -> {handle.shown} B handle "
              f"({handle.saved / handle.shown:.0f}x)")

        # C2 -- a question a prompt could not afford, answered by writing code.
        cell = await kernel.run(
            "sum(1 for r in run_rows if r['status'] == 'held')")
        expected = sum(1 for r in RUN if r["status"] == "held")
        answered = cell.result == str(expected)
        blind += not answered
        check("C2 a cell answers from the object", answered,
              f"held rows = {cell.result} (expected {expected})")

        # C3 -- and the answer, not the object, is what comes back.
        returned = len(cell.result or "")
        check("C3 only the answer crosses the wire", returned < 32,
              f"{returned} B returned, against {handle.saved:,} B held")

        # C4 -- the object outlives the cell that queried it.
        cell = await kernel.run("sorted({r['owner'] for r in run_rows})[:3]")
        check("C4 it persists between cells", cell.status == "ok", f"{cell.result}")

        # C5 -- a second query costs nothing to set up.
        cell = await kernel.run("run_rows[0]['exchange']['url']")
        check("C5 nested structure survives the trip", cell.result == "'/api/records/0'",
              f"{cell.result}")

    whole = len(json.dumps(RUN))
    print(f"\nLEAKED   handle not smaller than object : {leaked}   (must be 0)")
    print(f"BLIND    a cell could not answer        : {blind}   (must be 0)")
    print(f"FAILED   cases not matching             : {failed}")
    print(f"\nheld in the kernel {whole:,} B, entered the context {handle.shown} B")
    return 1 if leaked or blind or failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
