"""Does a published capability actually become callable, and does an incomplete one fail loudly?

    uv run python -m evals.capability.publish_eval

No browser and no site. The vendor's detection contract degrades a skill missing any of its
three files to markdown-only, so the case that matters is the negative one: an incomplete
layout must be refused here rather than warned about there.

    SILENT   an incomplete capability was accepted    must be 0
    DEAD     a complete one did not answer            must be 0
"""

from __future__ import annotations

import asyncio
import shutil
import sys
import tempfile
from pathlib import Path

from factory.capability.offer import NotInstallable, install, offer
from factory.capability.publish import Capability, complete, importable, write
from factory.kernel.driver import Kernel

#: A procedure of the shape `draft.py` will produce: parameters by diff, no model asked.
BODY = '''
async def run(rows: list[dict], status: str = "held") -> int:
    """Count the rows in a run whose status matches."""
    return sum(1 for row in rows if row.get("status") == status)
'''


async def run() -> int:
    silent = dead = failed = 0
    home = Path(tempfile.mkdtemp(prefix="factory-capability-"))

    def check(name: str, ok: bool, detail: str) -> None:
        nonlocal failed
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name:44} {detail}")

    try:
        # P1 -- the import name is derived, and a name that cannot be one is refused.
        check("P1 hyphens become underscores", importable("count-held") == "count_held",
              importable("count-held"))
        try:
            importable("2 bad names")
            refused = False
        except ValueError:
            refused = True
        check("P1 a non-identifier is refused", refused, "ValueError")

        it = Capability(name="count-held", description="Count held rows in a run.", body=BODY)
        root = write(home, it)
        check("P2 the contract is complete", complete(root),
              ", ".join(sorted(p.name for p in root.rglob("*") if p.is_file())))

        # P3 -- the negative case, which is the one the vendor degrades silently.
        broken = write(home, Capability(name="half-written", description="x", body=BODY))
        (broken / "pyproject.toml").unlink()
        accepted = True
        try:
            install(broken)
        except NotInstallable:
            accepted = False
        silent += accepted
        check("P3 an incomplete layout is refused", not accepted,
              "NotInstallable" if not accepted else "ACCEPTED IT")

        async with await Kernel.start() as kernel:
            await kernel.run("rows = [{'status': 'held'}, {'status': 'ok'}, {'status': 'held'}]")
            answer = await offer(kernel, root, "rows, 'held'")
            works = answer == "2"
            dead += not works
            check("P4 a cell calls the capability", works, f"count_held.run(...) -> {answer}")

            # P5 -- it is callable by name, the way the kernel exposes it.
            cell = await kernel.run("await count_held.run(rows, 'ok')")
            check("P5 the module-callable sugar is the TS host's", cell.result == "1",
                  f"a second .run() -> {cell.result}")

            # P6 -- the docstring is the capability's API and its CLI help, so it must
            # survive the trip. On `run`, not on the module: copying it up is the same TS
            # host wrapping P5 found missing.
            cell = await kernel.run("count_held.run.__doc__.strip()")
            carried = "Count the rows" in (cell.result or "")
            check("P6 the docstring survives, on run()", carried, (cell.result or "")[:46])

            # P7 -- and the signature, which is what makes it usable without reading source.
            cell = await kernel.run(
                "import inspect; str(inspect.signature(count_held.run))")
            typed = "rows" in (cell.result or "") and "status" in (cell.result or "")
            check("P7 the signature survives too", typed, (cell.result or "")[:46])
    finally:
        shutil.rmtree(home, ignore_errors=True)

    print(f"\nSILENT  an incomplete capability accepted : {silent}   (must be 0)")
    print(f"DEAD    a complete one did not answer     : {dead}   (must be 0)")
    print(f"FAILED  cases not matching                : {failed}")
    return 1 if silent or dead or failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
