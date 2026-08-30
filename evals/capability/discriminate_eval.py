"""Does a drafted capability's answer depend on what it was asked?

    uv run python -m evals.capability.discriminate_eval

No browser and no site. A recording door stands in for the BROWSER one: it answers every
act with ok and remembers what it was sent, which is the only thing this gate looks at. So
the whole chain runs -- draft, publish, install, a cell calling it through MCP -- with the
page replaced by a notebook.

    ADMITTED  a capability that ignores its arguments got through   must be 0
    REFUSED   one that plainly discriminates was rejected           must be 0
"""

from __future__ import annotations

import asyncio
import shutil
import socket
import sys
import tempfile
from pathlib import Path
from typing import Any

from evals.capability.draft_eval import WORKFLOW, a_run
from factory.capability.discriminate import discriminates, ignored
from factory.capability.draft import draft
from factory.capability.offer import offer
from factory.capability.publish import Capability, write
from factory.kernel.driver import Door, Kernel


def free_port() -> int:
    """A port the OS says is free, not one this file hopes is.

    Nothing outside this process needs to reach the door -- the kernel is handed the URL --
    so a fixed number buys nothing and costs a failure whenever a previous run's server has
    not let go. Measured: this suite failed under pytest for exactly that reason.
    """
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


PORT = free_port()
SENT: list[tuple[str, dict[str, Any]]] = []


def recording_door(name: str = "recording-door") -> Any:
    """Every verb the drafted body can call, answering ok and remembering the arguments."""
    from mcp.server.fastmcp import FastMCP

    app = FastMCP(name, host="127.0.0.1")
    app.settings.port = PORT

    def remember(verb: str, **args: str) -> dict[str, Any]:
        SENT.append((verb, args))
        return {"ok": True, "detail": f"recorded {verb}"}

    @app.tool()
    async def go(url: str) -> dict[str, Any]:
        """Record a navigation."""
        return remember("go", url=url)

    @app.tool()
    async def click(role: str, name: str) -> dict[str, Any]:
        """Record a press."""
        return remember("click", role=role, name=name)

    @app.tool()
    async def write(text: str) -> dict[str, Any]:
        """Record a write. FastMCP names the tool after the function, and the drafted body
        calls `write`, so this must be called that and nothing else."""
        return remember("write", text=text)

    return app


#: A capability that threads its parameter nowhere. The shape "did it reproduce" admits.
DEAF = Capability(
    name="ignores-its-argument", description="Looks like work, is not.",
    body='"""A procedure ignoring its arguments."""\n\n'
         "import rlm.mcp as mcp\n\n\n"
         "async def run(note: str) -> list[dict]:\n"
         '    """Always does the same thing."""\n'
         '    return [await mcp.call_tool("browser", "go", {"url": "http://127.0.0.1"})]\n')


async def run() -> int:
    admitted = refused = failed = 0
    home = Path(tempfile.mkdtemp(prefix="factory-discriminate-"))
    door: asyncio.Task[None] | None = None

    def check(name: str, ok: bool, detail: str) -> None:
        nonlocal failed
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name:48} {detail}")

    try:
        # C1 -- the static half, which needs nothing to run.
        real = draft(WORKFLOW, a_run(held=True))
        check("C1 a drafted capability uses its parameter", not ignored(real),
              f"ignored={sorted(ignored(real)) or 'none'}")
        deaf_params = ignored(DEAF)
        admitted += not deaf_params
        check("C1 one that ignores it is seen without running", deaf_params == {"note"},
              f"ignored={sorted(deaf_params)}")

        # C2 -- a static pass alone is not a pass.
        unrun = discriminates(real)
        check("C2 never having run is not a pass", not unrun, unrun.why())

        # C3 -- the behavioural half, through the whole chain onto a recording door.
        #: ONE DOOR FOR THE WHOLE RUN. `SENT` is shared, so a second server records into
        #: the same list and only competes for the port.
        door = asyncio.create_task(recording_door().run_streamable_http_async())
        await asyncio.sleep(2.0)

        wire = Door(name="browser", url=f"http://127.0.0.1:{PORT}/mcp")
        async with await Kernel.start(wire) as kernel:
            root = write(home, real)
            SENT.clear()
            await offer(kernel, root, "'hello'")
            first = list(SENT)
            SENT.clear()
            await kernel.run("await file_a_note.run('a different note')", timeout=60)
            second = list(SENT)

        check("C3 the capability reached the door", bool(first) and bool(second),
              f"{len(first)} acts, then {len(second)}")
        answer = discriminates(real, (first, second))
        refused += not answer
        check("C3 different inputs sent different acts", bool(answer), answer.why())

        written = [args.get("text") for verb, args in first + second if verb == "write"]
        check("C3 and the difference is the argument", written == ["hello", "a different note"],
              f"wrote {written}")

        # C4 -- the deaf one is refused end to end, not just by reading.
        deaf_root = write(home, DEAF)
        SENT.clear()
        async with await Kernel.start(wire) as kernel:
            await offer(kernel, deaf_root, "'one'")
            a = list(SENT)
            SENT.clear()
            await kernel.run("await ignores_its_argument.run('two')", timeout=60)
            b = list(SENT)
        verdict = discriminates(DEAF, (a, b))
        admitted += bool(verdict)
        check("C4 the deaf one is refused on both halves", not verdict, verdict.why())
    finally:
        #: However this ended. A leaked server holds its port into the next suite.
        if door is not None:
            door.cancel()
        shutil.rmtree(home, ignore_errors=True)

    print(f"\nADMITTED a capability that ignores its arguments : {admitted}   (must be 0)")
    print(f"REFUSED  one that discriminates was rejected     : {refused}   (must be 0)")
    print(f"FAILED   cases not matching                      : {failed}")
    return 1 if admitted or refused or failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
