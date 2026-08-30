"""Attach to a browser that is already running. Never launches a second one.

Playwright supplies attach, a maintained CDP transport, page lifecycle and response bodies.
It does NOT supply resolution: `get_by_role` returns a handle, and bridging a handle to the
node id the guard needs means marking the element, which is a DOM mutation a page can
watch. `Accessibility.queryAXTree` returns the id directly for one extra round trip.
"""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Any


def endpoint(port: int) -> str:
    """The browser's own CDP address, asked of the browser rather than assumed."""
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=10) as got:
        return json.load(got)["webSocketDebuggerUrl"]


@dataclass
class Attached:
    """One attached browser, and the pieces that outlive a single call."""

    playwright: Any
    browser: Any
    context: Any
    page: Any
    cdp: Any

    async def close(self) -> None:
        await self.playwright.stop()


async def attach(cdp_url: str) -> Attached:
    from playwright.async_api import async_playwright

    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp(cdp_url)
    context = browser.contexts[0]
    page = context.pages[0] if context.pages else await context.new_page()
    return Attached(playwright, browser, context, page, await context.new_cdp_session(page))
