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
    """Responses kept, on one CDP session.

    ONE STATE. What has been noticed and not yet fetched, and nothing else. An accumulator
    beside it was a second state with no reader: `drain` returned every response since the
    session opened, so a step inherited every earlier step's evidence and an act that was
    REFUSED came back CONFIRMED against a body the previous act had caused. Measured. The
    caller that reached in to `.clear()` it was the bug reported as a workaround.
    """

    def __init__(self) -> None:
        self._pending: dict[str, dict[str, Any]] = {}
        self._arrived: set[str] = set()

    def watch(self, cdp: Any) -> None:
        cdp.on("Network.responseReceived", self._noticed)
        cdp.on("Network.loadingFinished", self._arrival)
        cdp.on("Network.loadingFailed", self._arrival)

    def _noticed(self, message: dict[str, Any]) -> None:
        response = message.get("response", {})
        self._pending[message["requestId"]] = {
            "url": response.get("url", ""),
            "status": response.get("status", 0),
            "content_type": content_type(response.get("headers", {})),
        }

    def _arrival(self, message: dict[str, Any]) -> None:
        self._arrived.add(message["requestId"])

    def waiting(self) -> bool:
        return bool(self._pending.keys() - self._arrived)

    async def drain(self, cdp: Any) -> list[Exchange]:
        """Fetch the bodies worth keeping. Safe here, never inside the handler.

        THE SIZE IS THE BODY'S. `encodedDataLength` reported 104 bytes for three files of
        different sizes, so the cap is applied to what actually came back.
        """
        taken = {rid: seen for rid, seen in self._pending.items() if rid in self._arrived}
        for request_id in taken:
            del self._pending[request_id]
            self._arrived.discard(request_id)
        drained: list[Exchange] = []
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
            drained.append(Exchange(
                url=seen["url"], status=seen["status"],
                content_type=seen["content_type"], size=size, body=body))
        return drained


def _self_check() -> None:
    """Two drains are disjoint, and a drain with nothing pending is empty.

        uv run python -m factory.browser.bodies
    """
    import asyncio

    class Answering:
        async def send(self, method: str, params: dict[str, Any]) -> dict[str, str]:
            return {"body": '[{"id": "1"}]'}

    async def check() -> None:
        header = {"Content-Type": "application/json"}

        def answered(kept: Bodies, request_id: str, url: str, *, arrived: bool) -> None:
            kept._noticed({"requestId": request_id,
                           "response": {"url": url, "status": 200, "headers": header}})
            if arrived:
                kept._arrival({"requestId": request_id})

        kept = Bodies()
        answered(kept, "1", "first", arrived=True)
        first = await kept.drain(Answering())
        answered(kept, "2", "second", arrived=True)
        second = await kept.drain(Answering())

        assert [e.url for e in first] == ["first"], first
        assert [e.url for e in second] == ["second"], "a drain returns only what it took"
        assert await kept.drain(Answering()) == [], "nothing pending, nothing drained"
        assert first[0].records() == [{"id": "1"}], "the body parses where the reader will"

        waiting = Bodies()
        answered(waiting, "3", "in flight", arrived=False)
        assert await waiting.drain(Answering()) == [], "in flight is held, not emitted empty"
        waiting._arrival({"requestId": "3"})
        landed = await waiting.drain(Answering())
        assert [e.url for e in landed] == ["in flight"], landed
        assert landed[0].body, "and it arrives with its body, on the drain after"
        print("bodies: drains are disjoint, an empty drain is empty, and a body in flight "
              "is held until its bytes land rather than emitted blank")

    asyncio.run(check())


if __name__ == "__main__":
    _self_check()
