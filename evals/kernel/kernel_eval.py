"""What can a cell reach, and can we get the runtime back?

    uv run python -m evals.kernel.kernel_eval

No browser, no network, no site. Every case runs real code in the real runtime, because
isolation asserted from the spawn side is isolation nobody checked -- an environment
scrubbed in one place and inherited in another looks identical from the call site.

    ESCAPED   a cell reached something it must not     must be 0
    WEDGED    the runtime did not come back            must be 0
"""

from __future__ import annotations

import asyncio
import os
import sys

from factory.kernel.driver import Kernel

#: Planted in the parent's environment for the duration of the run. If a cell can read it,
#: it could read the real one, and nothing else about the spawn matters.
CANARY = "FACTORY_KERNEL_CANARY"


async def run() -> int:
    os.environ[CANARY] = "a-secret-the-cell-must-not-see"
    os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-not-a-real-key")
    escaped = wedged = failed = 0

    def check(name: str, ok: bool, detail: str) -> None:
        nonlocal failed
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name:34} {detail}")

    async with await Kernel.start() as kernel:
        print(f"runtime python {kernel.python}\n")

        # K1 -- a cell cannot read a secret.
        cell = await kernel.run(
            f"import os; (os.environ.get({CANARY!r}), os.environ.get('ANTHROPIC_API_KEY'))")
        leaked = cell.result != "(None, None)"
        escaped += leaked
        check("K1 no secret reaches a cell", not leaked, f"cell saw {cell.result}")

        # K2 -- a cell cannot import the factory.
        cell = await kernel.run("import factory")
        reachable = cell.status == "ok"
        escaped += reachable
        check("K2 the factory is not importable", not reachable,
              f"{cell.ename or 'IMPORTED'}")

        # K3a -- top-level await.
        cell = await kernel.run("import asyncio\nawait asyncio.sleep(0)\n'awaited'")
        check("K3 top-level await", cell.result == "'awaited'", f"result={cell.result}")

        # K3b -- a task outlives the cell that made it.
        await kernel.run(
            "import asyncio\n"
            "seen = []\n"
            "async def tick():\n"
            "    while True:\n"
            "        seen.append(1); await asyncio.sleep(0.01)\n"
            "task = asyncio.create_task(tick())")
        await kernel.run("await asyncio.sleep(0.2)")
        cell = await kernel.run("len(seen) > 1")
        check("K3 a task survives its cell", cell.result == "True", f"result={cell.result}")

        # K4 -- interrupt lands, and the runtime keeps serving.
        cell = await kernel.run("import time\nwhile True: time.sleep(0.01)", timeout=2.0)
        landed = cell.interrupted
        check("K4 an interrupt lands", landed, f"{cell.ename} after {cell.seconds:.1f}s")
        after = await kernel.run("'still here'")
        alive = after.result == "'still here'"
        wedged += not alive
        check("K4 the runtime keeps serving", alive, f"next cell -> {after.result}")

        # K5 -- a hung cell is bounded by us. An await-suspended cell cannot be reached by
        # SIGINT, so the runtime cancels the task instead; either way it must come back.
        cell = await kernel.run("import asyncio\nawait asyncio.sleep(3600)", timeout=2.0)
        bounded = cell.status == "error"
        check("K5 a hung cell is bounded", bounded,
              f"{cell.ename or 'returned ok'} after {cell.seconds:.1f}s")
        after = await kernel.run("'recovered'")
        alive = after.result == "'recovered'"
        wedged += not alive
        check("K5 and recoverable", alive, f"next cell -> {after.result}")

        # K6 -- what a round trip costs.
        warm = [await kernel.run("None") for _ in range(5)]
        each = sorted(c.seconds for c in warm)[len(warm) // 2] * 1000
        check("K6 round trip measured", True, f"{each:.1f} ms median over 5 trivial cells")

    print(f"\nESCAPED  a cell reached something it must not : {escaped}   (must be 0)")
    print(f"WEDGED   the runtime did not come back       : {wedged}   (must be 0)")
    print(f"FAILED   cases not matching expectation      : {failed}")
    return 1 if escaped or wedged or failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
