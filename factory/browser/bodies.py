"""What a page fetched for itself, on the CDP session that is already open.

Plain CDP, no extension point: nothing here rides a vendor's internals, which is what makes
the BROWSER driver a tier-1 dependency rather than a tier-2 extend.

DEADLOCK, AND IT IS A REAL CDP RULE. `getResponseBody` is a request, and issuing one from
inside a handler for an event on the same connection hangs forever -- the client is inside
its own dispatch loop and cannot process the reply. So the handler records and `drain`
fetches.
"""

from __future__ import annotations

from typing import Any

from factory.core.evidence import STRUCTURED, Exchange

#: Filters on HTTP metadata and never on content. A body is read because of what it is, not
#: because of what it says, so nothing here knows a site.
TOO_BIG = 32_000


def content_type(headers: dict[str, str]) -> str:
    """CDP preserves the server's header casing, so the lookup cannot be exact.

    Measured: a `Content-Type: application/json` response read as `''`, and every body was
    discarded, on a filter that looked for `content-type`.
    """
    for key, value in headers.items():
        if key.lower() == "content-type":
            return value.split(";")[0].strip().lower()
    return ""


def worth_reading(kind: str) -> bool:
    return any(mark in kind for mark in STRUCTURED)


class Bodies:
    """Responses kept, on one CDP session."""

    def __init__(self) -> None:
        self.exchanges: list[Exchange] = []
        self._pending: dict[str, dict[str, Any]] = {}

    def watch(self, cdp: Any) -> None:
        cdp.on("Network.responseReceived", self._noticed)

    def _noticed(self, message: dict[str, Any]) -> None:
        response = message.get("response", {})
        self._pending[message["requestId"]] = {
            "url": response.get("url", ""),
            "status": response.get("status", 0),
            "content_type": content_type(response.get("headers", {})),
        }

    async def drain(self, cdp: Any) -> list[Exchange]:
        """Fetch the bodies worth keeping. Safe here, never inside the handler.

        THE SIZE IS THE BODY'S. `encodedDataLength` reported 104 bytes for three files of
        different sizes, so the cap is applied to what actually came back.
        """
        taken, self._pending = self._pending, {}
        for request_id, seen in taken.items():
            body, size = None, 0
            if worth_reading(seen["content_type"]):
                #: A body is evicted once the page navigates, and asking for one that is
                #: gone is ordinary rather than exceptional. It costs the body, not the run.
                try:
                    got = await cdp.send("Network.getResponseBody", {"requestId": request_id})
                    body = got.get("body")
                except Exception:
                    body = None
                if body is not None:
                    size = len(body)
                    if size > TOO_BIG:
                        body = None
            self.exchanges.append(Exchange(
                url=seen["url"], status=seen["status"],
                content_type=seen["content_type"], size=size, body=body))
        return self.exchanges
