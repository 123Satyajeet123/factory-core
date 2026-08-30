"""Can an act be confirmed by evidence a DIFFERENT act caused?

    uv run python -m evals.witness.stale_eval

WHY THIS IS NOT IN `witness_eval`. That suite builds a `Did` by hand and asks the ladder
what it says, which is the right way to check a verdict and cannot see where the evidence
came from. This one runs the collector, so the `Did` is assembled the way the driver
assembles it -- and the defect it exists to catch lived in neither driver but in the seam
between them.

MEASURED, BEFORE IT WAS FIXED. `Bodies` kept a second accumulator beside its pending set
and `drain` returned every response since the session opened. A press the guard correctly
REFUSED came back CONFIRMED against the body the press before it had caused: false
confirmed, on the one number the witness suite requires to be zero, from a driver whose own
suite was green.

BOTH DIRECTIONS. An act that really did cause its evidence must still confirm, or this
passes with the collector deleted.
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any

from factory.browser.bodies import Bodies
from factory.core.contract import Contract, Verdict
from factory.core.evidence import Delivery, Did
from factory.witness.ladder import Ladder
from factory.witness.readers.fetched import Fetched

WROTE = '[{"id": "883974", "name": "Ada Lovelace"}]'
JSON = {"Content-Type": "application/json"}


class Answering:
    """A CDP that reports a response the way the browser does. Nothing here is a browser.

    DRIVEN THROUGH `watch`, NOT THROUGH `_pending`. A first version poked the collector's
    internals and went blind the day it grew a second precondition -- a body is not
    fetchable until `Network.loadingFinished`. An eval that reaches past the surface it is
    testing stops testing it.
    """

    def __init__(self) -> None:
        self.handlers: dict[str, Any] = {}

    def on(self, event: str, handler: Any) -> None:
        self.handlers[event] = handler

    def fetched(self, request_id: str, url: str) -> None:
        self.handlers["Network.responseReceived"]({
            "requestId": request_id,
            "response": {"url": url, "status": 200, "headers": JSON}})
        self.handlers["Network.loadingFinished"]({"requestId": request_id})

    async def send(self, method: str, params: dict[str, Any]) -> dict[str, str]:
        return {"body": WROTE}


async def run() -> int:
    kept, cdp = Bodies(), Answering()
    kept.watch(cdp)
    ladder = Ladder([Fetched()])
    contract = Contract(expects={"name": "Ada Lovelace"})

    #: Act one writes, and the destination answers.
    cdp.fetched("1", "/rows")
    wrote = Did(ok=True, delivery=Delivery.TARGET_HIT, exchanges=await kept.drain(cdp))
    caused = ladder.witness(wrote, contract)

    #: Act two is REFUSED. Nothing was dispatched, so nothing was fetched.
    refused = Did(ok=False, delivery=Delivery.INTERCEPTED, detail="covered",
                  exchanges=await kept.drain(cdp))
    inherited = ladder.witness(refused, contract)

    false_confirmed = inherited.verdict is Verdict.CONFIRMED
    blind = caused.verdict is not Verdict.CONFIRMED

    print(f"the act that wrote      : {caused.verdict}  ({caused.why})")
    print(f"the act that was refused: {inherited.verdict}  ({inherited.why})")
    print(f"  it carried {len(refused.exchanges)} exchanges (must be 0)")
    print(f"\nFALSE CONFIRMED  an act confirmed by another act's evidence : "
          f"{int(false_confirmed)}   (must be 0)")
    print(f"BLIND            an act that did happen was not confirmed   : {int(blind)}")
    return 1 if false_confirmed or blind else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
