"""The door a KERNEL cell reaches the page through, and the only one.

WHY A DOOR AT ALL. A cell is model-written code running in another interpreter with its own
venv, so it cannot import this package. Left to itself it would open its own connection to
the browser, and every guarantee this driver makes -- travel, the hit test, the kept
response bodies, the witness -- would become optional. They are not optional. Everything
offered here is already guarded, so an act a model causes is guarded because of where it
came from rather than because the model chose well.

WHAT IS DELIBERATELY NOT OFFERED: raw CDP, coordinates, selectors, and any way to dispatch
without the guard. browser-use ships an MCP server whose `browser_click` takes
`coordinate_x`/`coordinate_y`; that is the shape this one exists to not be.

STREAMABLE HTTP ON LOOPBACK, NOT STDIO. Over stdio the kernel would spawn this process, and
it would have to attach its own client to the browser -- two sessions, and the response
bodies split across them. In the factory's own process there is one Browser, one session
and one evidence channel. `rlm.mcp` speaks both transports; this one needs the shared state.

NOTHING HERE KNOWS A DESTINATION. The verbs are `core.verbs`, and a url is something a
caller passes rather than something this file contains.
"""

from __future__ import annotations

from typing import Any

from factory.browser.driver import Browser
from factory.core.workflow import Target

#: Loopback only. A door reachable from another host is not a door, it is a hole.
HOST = "127.0.0.1"


def door(browser: Browser, *, name: str = "factory-browser") -> Any:
    """An MCP server over one already-attached browser."""
    from mcp.server.fastmcp import FastMCP

    app = FastMCP(name, host=HOST)

    @app.tool()
    async def candidates() -> list[str]:
        """Everything on the page that can be acted on, as role and name."""
        from factory.browser import locate

        return sorted(locate.offered(await browser.candidates()).values())

    @app.tool()
    async def click(role: str, name: str) -> dict[str, Any]:
        """Press a control by what it is. Refuses unless exactly one thing matches.

        The press travels, is re-measured at the point it will land on, and is not sent if
        something else is there.
        """
        return (await browser.click(Target(role=role, name=name))).model_dump(mode="json")

    @app.tool()
    async def write(text: str) -> dict[str, Any]:
        """Type into whatever holds focus, key by key."""
        return (await browser.type(text)).model_dump(mode="json")

    @app.tool()
    async def go(url: str) -> dict[str, Any]:
        """Navigate, and report where the tab actually ended up."""
        return (await browser.go(url)).model_dump(mode="json")

    @app.tool()
    async def fetched() -> list[dict[str, Any]]:
        """What the page fetched for itself: the channel that did not perform the act."""
        return [e.model_dump(mode="json") for e in await browser.fetched()]

    return app


async def serve(browser: Browser, port: int) -> None:
    """Run the door until cancelled."""
    app = door(browser)
    app.settings.port = port
    await app.run_streamable_http_async()
