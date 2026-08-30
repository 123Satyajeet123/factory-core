
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel


class Door(BaseModel):

    name: str
    url: str

    def config(self) -> dict[str, Any]:
        return {"type": "http", "url": self.url}


class Bridge:

    def __init__(self, *doors: Door) -> None:
        self.doors = {door.name: door for door in doors}
        self._handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
            "mcp.config": self._config,
            "mcp.refresh": self._refresh,
        }

    def answer(self, data: dict[str, Any]) -> dict[str, Any]:
        handler = self._handlers.get(str(data.get("type", "")))
        if handler is None:
            return {"status": "error", "error": f"no handler for {data.get('type')!r}"}
        return handler(data)

    def _config(self, data: dict[str, Any]) -> dict[str, Any]:
        door = self.doors.get(str(data.get("server", "")))
        if door is None:
            return {"status": "error",
                    "error": f"server {data.get('server')!r} is not declared by the host"}
        return {"status": "ok", "result": door.config()}

    def _refresh(self, data: dict[str, Any]) -> dict[str, Any]:
        return {"status": "ok", "result": {}}
