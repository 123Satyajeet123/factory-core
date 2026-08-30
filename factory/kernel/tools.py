"""What a cell may reach, and the only place that decides it.

THE HOST IS THE REGISTRY, AND THAT IS THE WHOLE SECURITY PROPERTY. `rlm.mcp` does not read
a settings file: `_config()` asks the host over the protocol -- `host_request("mcp.config",
{"server": ...})` -- and waits. So a cell cannot declare a server, cannot edit a config a
later cell would read, and cannot point a name at a different URL. It can ask for a name,
and a name this bridge does not hold is an error.

That is why `browser/serve.py` is reachable and raw CDP is not: the door is the only thing
ever named here, and everything it offers is already guarded.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel


class Door(BaseModel):
    """One MCP server the host is willing to name, and where it answers."""

    name: str
    url: str

    def config(self) -> dict[str, Any]:
        """What `rlm.mcp` needs to open a transport.

        No `oauth` and no `bearerTokenEnvVar`: on loopback the runtime resolves an
        anonymous identity and sends no Authorization header. A door that needed a secret
        would mean handing a cell one, which is the thing `venv.environment()` prevents.
        """
        return {"type": "http", "url": self.url}


class Bridge:
    """Answers the runtime's typed host requests. Nothing else answers them."""

    def __init__(self, *doors: Door) -> None:
        self.doors = {door.name: door for door in doors}
        self._handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
            "mcp.config": self._config,
            "mcp.refresh": self._refresh,
        }

    def answer(self, data: dict[str, Any]) -> dict[str, Any]:
        """One reply envelope, always. An unknown request type is refused, not ignored.

        Ignoring would leave the cell awaiting a reply that never comes, which reads as a
        hung cell and would be diagnosed in the wrong place.
        """
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
        """Nothing to refresh: a loopback door carries no credential to expire."""
        return {"status": "ok", "result": {}}
