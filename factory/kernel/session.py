
from __future__ import annotations

import asyncio
import contextlib
import itertools
import json
import subprocess
import threading
import time
from typing import Any

from factory.core.errors import KernelFailed
from factory.kernel import protocol, venv
from factory.kernel.protocol import Cell, Status
from factory.kernel.tools import Bridge


class KernelError(KernelFailed):
    pass


GONE = {"event": "__gone__"}


class Session:

    def __init__(self, bridge: Bridge | None = None) -> None:
        self._bridge = bridge or Bridge()
        self._process: subprocess.Popen[str] | None = None
        self._frames: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._ids = itertools.count(1)
        self.python = ""

    async def start(self, *, timeout: float = 30.0) -> Session:
        if not venv.ready():
            venv.build()
        self._process = subprocess.Popen(
            [str(venv.interpreter()), "-m", "rlm.repl"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, bufsize=1, env=venv.environment(), cwd=str(venv.VENV))
        loop = asyncio.get_running_loop()
        threading.Thread(target=self._read, args=(loop,), daemon=True).start()

        ready = await self._await_frame(lambda f: f.get("event") == "ready", timeout)
        if ready.get("protocol") != protocol.PROTOCOL:
            await self.close()
            raise KernelError(
                f"runtime speaks protocol {ready.get('protocol')}, "
                f"this driver speaks {protocol.PROTOCOL}")
        self.python = ready.get("python", "")
        return self

    def _read(self, loop: asyncio.AbstractEventLoop) -> None:
        assert self._process and self._process.stdout
        for line in self._process.stdout:
            if not line.strip():
                continue
            try:
                frame = json.loads(line)
            except ValueError:
                continue  # the runtime answers a malformed line itself; ours cannot be one
            loop.call_soon_threadsafe(self._deliver, frame)
        loop.call_soon_threadsafe(self._frames.put_nowait, GONE)

    def _deliver(self, frame: dict[str, Any]) -> None:
        if frame.get("event") == "host_request":
            answer = self._bridge.answer(frame.get("data") or {})
            with contextlib.suppress(KernelError, OSError):
                self._send({"type": "host_reply", "id": frame.get("id"), "data": answer})
            return
        self._frames.put_nowait(frame)

    def _send(self, request: dict[str, Any]) -> None:
        if not self._process or self._process.poll() is not None:
            raise KernelError("the runtime is not running")
        assert self._process.stdin
        self._process.stdin.write(json.dumps(request) + "\n")
        self._process.stdin.flush()

    async def _await_frame(self, wanted: Any, timeout: float) -> dict[str, Any]:
        async with asyncio.timeout(timeout):
            while True:
                frame = await self._frames.get()
                if frame is GONE:
                    raise KernelError("the runtime exited before it announced itself")
                if wanted(frame):
                    return frame

    async def run(self, code: str, *, timeout: float = 30.0,
                  grace: float = 5.0) -> Cell:
        cell_id = str(next(self._ids))
        cell = Cell(id=cell_id, status=Status.OK)
        started = time.perf_counter()
        if not self.alive:
            return cell.model_copy(update={
                "status": Status.ERROR, "ename": "Died",
                "evalue": "the runtime is not running", "seconds": 0.0})
        self._send(protocol.execute(cell_id, code))

        try:
            await self._collect(cell, timeout)
        except TimeoutError:
            with contextlib.suppress(KernelError, OSError):
                self._send(protocol.interrupt(cell_id))
            try:
                await self._collect(cell, grace)
            except TimeoutError:
                cell.status, cell.ename = Status.ERROR, "Hung"
                cell.evalue = f"no done after {timeout}s and no interrupt after {grace}s"
        cell.seconds = time.perf_counter() - started
        return cell

    async def _collect(self, cell: Cell, timeout: float) -> None:
        async with asyncio.timeout(timeout):
            while True:
                frame = await self._frames.get()
                event, at = frame.get("event"), frame.get("id")
                if frame is GONE:
                    cell.status, cell.ename = Status.ERROR, "Died"
                    cell.evalue = "the runtime exited while this cell was running"
                    return
                if event == "done" and at == cell.id:
                    cell.status = Status(frame.get("status", "error"))
                    return
                if at not in (cell.id, None):
                    continue
                if event == "stdout":
                    cell.out.append(frame.get("text", ""))
                elif event == "stderr":
                    cell.err.append(frame.get("text", ""))
                elif event == "result":
                    cell.result = frame.get("text")
                elif event == "error":
                    cell.ename = frame.get("ename", "")
                    cell.evalue = frame.get("evalue", "")
                    cell.traceback = frame.get("traceback", [])

    @property
    def alive(self) -> bool:
        return self._process is not None and self._process.poll() is None

    async def interrupt(self) -> None:
        self._send(protocol.interrupt())

    async def close(self) -> None:
        if not self._process:
            return
        with contextlib.suppress(KernelError, OSError):
            self._send(protocol.shutdown())
        with contextlib.suppress(subprocess.TimeoutExpired):
            self._process.wait(timeout=5)
        if self._process.poll() is None:
            self._process.kill()
        self._process = None
