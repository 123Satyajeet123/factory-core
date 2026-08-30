"""The KERNEL driver: code to effects, in an interpreter that is not ours.

THE ONLY THING IN THIS TREE THAT SPAWNS A RUNTIME. Everything above it hands over source
and receives a typed `Cell`; nothing above it knows a frame, a file descriptor or a pid.

A cell holds none of our keys and cannot import this package -- see gates/kernel-isolation.md
and `venv.environment()`. That is what makes it safe to run code a model wrote, and it is
the reason the door in `browser/serve.py` exists rather than a shared import.
"""

from __future__ import annotations

from pathlib import Path

from factory.kernel import skills
from factory.kernel.protocol import Cell
from factory.kernel.session import KernelError, Session
from factory.kernel.skills import (
    NotInstallable,
)
from factory.kernel.skills import install as _install
from factory.kernel.tools import Bridge, Door

__all__ = ["Bridge", "Cell", "Door", "Kernel", "KernelError", "NotInstallable"]


class Kernel:
    """One live runtime, driven."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @classmethod
    async def start(cls, *doors: Door, timeout: float = 30.0) -> Kernel:
        """Build the interpreter if it is missing, spawn it, and shake hands.

        Every door named here is one a cell may reach and the only ones it may reach.
        With none, a cell runs code and can name no server at all.
        """
        return cls(await Session(Bridge(*doors)).start(timeout=timeout))

    @property
    def alive(self) -> bool:
        """Whether the runtime is still there. A cell against a dead one comes back
        `ename="Died"` rather than raising, so this is how a caller decides to restart."""
        return self._session.alive

    @property
    def python(self) -> str:
        """The runtime's own version, as it announced itself."""
        return self._session.python

    async def run(self, code: str, *, timeout: float = 30.0) -> Cell:
        """One cell. Top-level `await` is allowed and a task it starts outlives it."""
        return await self._session.run(code, timeout=timeout)

    async def install(self, root: Path) -> None:
        """Put a package in this kernel's interpreter and make this process see it.

        The refresh is not optional and not the caller's to remember: without it the name
        stays unimportable in a kernel that was already running.
        """
        _install(root)
        cell = await self.run(skills.REFRESH, timeout=60)
        if cell.status != "ok":
            raise NotInstallable(f"could not refresh the import path: {cell.evalue}")

    async def interrupt(self) -> None:
        return await self._session.interrupt()

    async def close(self) -> None:
        return await self._session.close()

    async def __aenter__(self) -> Kernel:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()
