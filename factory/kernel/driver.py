
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

    def __init__(self, session: Session) -> None:
        self._session = session

    @classmethod
    async def start(cls, *doors: Door, timeout: float = 30.0) -> Kernel:
        return cls(await Session(Bridge(*doors)).start(timeout=timeout))

    @property
    def alive(self) -> bool:
        return self._session.alive

    @property
    def python(self) -> str:
        return self._session.python

    async def run(self, code: str, *, timeout: float = 30.0) -> Cell:
        return await self._session.run(code, timeout=timeout)

    async def install(self, root: Path) -> None:
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
