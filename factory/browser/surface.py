"""Which surface an act happened on, and which page that is now.

A SURFACE IS ITS ORIGIN, and that is recorded rather than written. `scheme://host` comes
off the page the person was using, the same way `Target.role` and `Target.name` do. It is
evidence, not a table: nothing in this file names a destination, and adding one would be
the failure `evals/agnostic` exists to catch.

WHY NOT A TAB INDEX. Tabs are reordered, closed and reopened between a demonstration and a
replay. An index is a fact about one afternoon; an origin is a fact about the work.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse


def of(url: str) -> str:
    """The surface a url belongs to."""
    seen = urlparse(url)
    return f"{seen.scheme}://{seen.netloc}" if seen.netloc else ""


def among(pages: list[Any], surface: str) -> Any | None:
    """The page showing that surface, or nothing.

    ZERO OR TWO IS NOT AN ANSWER, and for the same reason `locate` refuses on both: acting
    on the wrong surface is indistinguishable from working until something is typed into
    somebody else's tab.
    """
    if not surface:
        return None
    showing = [page for page in pages if of(page.url) == surface]
    return showing[0] if len(showing) == 1 else None
