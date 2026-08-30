"""The KERNEL driver: code to effects, in an interpreter that is not ours.

THE ONLY THING IN THIS TREE THAT SPAWNS A RUNTIME. Everything above it hands over source
and receives a typed `Cell`; nothing above it knows a frame, a file descriptor or a pid.

A cell holds none of our keys and cannot import this package -- see gates/kernel-isolation.md
and `venv.environment()`. That is what makes it safe to run code a model wrote, and it is
the reason the door in `browser/serve.py` exists rather than a shared import.
"""

from __future__ import annotations

from factory.kernel.protocol import Cell
from factory.kernel.session import KernelError, Session
from factory.kernel.tools import Bridge, Door

__all__ = ["Bridge", "Cell", "Door", "Kernel", "KernelError"]


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
    def python(self) -> str:
        """The runtime's own version, as it announced itself."""
        return self._session.python

    async def run(self, code: str, *, timeout: float = 30.0) -> Cell:
        """One cell. Top-level `await` is allowed and a task it starts outlives it."""
        return await self._session.run(code, timeout=timeout)

    async def interrupt(self) -> None:
        return await self._session.interrupt()

    async def close(self) -> None:
        return await self._session.close()

    async def __aenter__(self) -> Kernel:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()
