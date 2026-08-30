"""Can an irreversible act happen without a person having allowed it?

    uv run python -m evals.authority.permit_eval

gates/permits.md. No browser: the driver is a stand-in that counts what it was asked to do,
so "the act did not happen" is measured at the driver rather than inferred from a verdict.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime, timedelta

from factory.authority import permit as permits
from factory.browser.locate import Found
from factory.core.evidence import Did
from factory.core.verbs import Doing
from factory.core.workflow import Step, Target, Workflow
from factory.memory.driver import Memory
from factory.run import harness


class Counting:
    """A driver that does nothing and remembers being asked.

    ITS SIGNATURES MATCH THE REAL DRIVER'S, AND THAT IS NOT COSMETIC. `find` took one
    argument here while `browser/driver.py` takes two; nothing noticed until `run/select.py`
    was wired in and passed the second. A stub that has drifted from the interface it stands
    in for tests the stub.
    """

    def __init__(self) -> None:
        self.asked: list[str] = []
        self._last = Target()

    async def on(self, _surface: str) -> bool:
        return True

    async def next_row(self) -> None:
        return None

    async def find(self, target: Target, _chooser: object = None) -> Found:
        self._last = target
        return Found(backend_node_id=1, rung="structural", resolved=target)

    async def press(self, _found: Found) -> Did:
        self.asked.append(self._last.described())
        return Did(ok=True, detail="pressed")


SEND = Step(doing=Doing.PRESS, intent="send it", irreversible=True,
            target=Target(role="button", name="Send"))
FLOW = Workflow(name="outreach", steps=[SEND], params=("who",))
ROWS = [{"who": "a"}, {"who": "b"}, {"who": "c"}]


async def run() -> int:
    faults = 0

    #: A3 and A7. Nobody granted anything, and nobody is there to ask.
    driver, memory = Counting(), Memory()
    done = await harness.over(driver, FLOW, ROWS, memory=memory)
    refused = [r for r in done.rows if r.refused]
    print(f"no permit         acts={len(driver.asked)} rows refused={len(refused)}")
    if driver.asked:
        faults += 1
        print("FAULT an irreversible act happened with no permit")
    if len(refused) != len(ROWS) or not refused[0].refused.about:
        faults += 1
        print("FAULT a refusal must carry what is being asked, in the act's own words")
    print(f"   asks: {refused[0].refused.about!r}")

    #: A7 again, sharper: no memory at all is not permission.
    bare = Counting()
    await harness.over(bare, FLOW, ROWS)
    if bare.asked:
        faults += 1
        print("FAULT with nowhere to hold a permit, the act still happened")

    #: A2. Two granted, three asked for.
    driver, memory = Counting(), Memory()
    permits.grant(memory, SEND, FLOW.name, times=2)
    done = await harness.over(driver, FLOW, ROWS, memory=memory)
    left = permits.held(memory, SEND, FLOW.name)
    print(f"granted 2 of 3    acts={len(driver.asked)} "
          f"refused={sum(1 for r in done.rows if r.refused)} left={left.left if left else 0}")
    if len(driver.asked) != 2:
        faults += 1
        print(f"FAULT a permit for two authorised {len(driver.asked)}")

    #: A5. Withdrawn between rows.
    driver, memory = Counting(), Memory()
    permits.grant(memory, SEND, FLOW.name, times=9)
    await harness.over(driver, FLOW, ROWS[:1], memory=memory)
    permits.revoke(memory, SEND, FLOW.name)
    await harness.over(driver, FLOW, ROWS[1:], memory=memory)
    print(f"revoked after one act={len(driver.asked)}")
    if len(driver.asked) != 1:
        faults += 1
        print("FAULT revocation did not take effect on the next act")

    #: Expiry is not a countdown somebody forgot to run.
    memory = Memory()
    stale = permits.grant(memory, SEND, FLOW.name, times=9, days=1)
    expired = stale.model_copy(update={"until": datetime.now(UTC) - timedelta(seconds=1)})
    print(f"expired permit    good={expired.good()} left={expired.left}")
    if expired.good():
        faults += 1
        print("FAULT an expired permit still answers")

    #: A4. A permit for one workflow authorises nothing in another.
    driver, memory = Counting(), Memory()
    permits.grant(memory, SEND, "something else", times=9)
    await harness.over(driver, FLOW, ROWS, memory=memory)
    print(f"other workflow    acts={len(driver.asked)}")
    if driver.asked:
        faults += 1
        print("FAULT a permit granted elsewhere authorised this")

    print(f"\nFAULTS  irreversible acts nobody allowed : {faults}   (must be 0)")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
