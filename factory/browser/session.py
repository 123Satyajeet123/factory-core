"""Attach to a browser that is already running. Never launches a second one.

BrowserSession(cdp_url=...) imports without the Agent or any LLM client, so the actuator
is reachable with none of the vendor's model machinery loaded.
"""

from __future__ import annotations

import json
import urllib.request
from typing import Any


def endpoint(port: int) -> str:
    """The browser's own CDP address, asked of the browser rather than assumed."""
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=10) as got:
        return json.load(got)["webSocketDebuggerUrl"]


async def attach(cdp_url: str) -> Any:
    """A started BrowserSession over an existing browser."""
    from browser_use.browser.session import BrowserSession

    session = BrowserSession(cdp_url=cdp_url)
    await session.start()
    return session
