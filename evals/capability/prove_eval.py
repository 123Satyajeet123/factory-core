"""Is a capability that replays without error proven?

    uv run python -m evals.capability.prove_eval

No browser and no site. Fixture readers, the way `evals/witness` uses them: what is under
test is whether replaying counts as evidence, not whether any particular reader works.

    CREDULOUS  a replay with nobody watching was called proven   must be 0
    BLIND      a destination that confirmed it was not believed  must be 0
"""

from __future__ import annotations

import sys

from factory.capability.prove import Proven, prove
from factory.core.contract import Contract, Reading
from factory.core.evidence import Did
from factory.witness.channel import Channel
from factory.witness.ladder import Ladder

CONTRACT = Contract(expects={"id": "77", "status": "filed"})
ALL = frozenset({"id", "status"})


class Says:
    """A fixture reader. In an eval a stand-in is a fixture; shipped, it would be product."""

    def __init__(self, name: str, channel: Channel, values: dict[str, str],
                 readable: frozenset[str]) -> None:
        self.name, self.channel = name, channel
        self._values, self._readable = values, readable

    def read(self, did: Did, contract: Contract) -> Reading:
        return Reading(values=dict(self._values), readable=self._readable)


def replayed(*ok: bool) -> list[dict]:
    """What a drafted capability returns: what each act reported."""
    return [Did(ok=held, detail="acted").model_dump(mode="json") for held in ok]


def run() -> int:
    credulous = blind = failed = 0

    def check(name: str, ok: bool, detail: str) -> None:
        nonlocal failed
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name:52} {detail}")

    filed = Ladder([Says("asked", Channel.DESTINATION, {"id": "77", "status": "filed"}, ALL)])
    denies = Ladder([Says("asked", Channel.DESTINATION, {"id": "77", "status": "draft"}, ALL)])
    cannot = Ladder([Says("fetched", Channel.WIRE, {}, frozenset())])
    ours = Ladder([Says("serialised", Channel.DOM, {"id": "77", "status": "filed"}, ALL)])

    # P1 -- the destination agrees. This is the only thing that proves anything.
    good = prove("files", replayed(True, True, True), CONTRACT, filed)
    blind += not good
    check("P1 the destination confirming is proof", bool(good), good.line())

    # P2 -- THE INVERTED FILTER. A clean replay with nobody watching is not proof.
    alone = prove("files", replayed(True, True, True), CONTRACT, None)
    credulous += bool(alone)
    check("P2 a replay with no witness proves nothing",
          alone.standing is Proven.UNPROVEN, alone.line())

    # P3 -- nor is a replay watched by a channel that cannot see the fields.
    unseen = prove("files", replayed(True, True), CONTRACT, cannot)
    credulous += bool(unseen)
    check("P3 nor one no reader could address",
          unseen.standing is Proven.UNPROVEN, unseen.line())

    # P4 -- nor one watched only by a channel we authored.
    mirror = prove("files", replayed(True), CONTRACT, ours)
    credulous += bool(mirror)
    check("P4 nor one watched by a channel we authored",
          mirror.standing is Proven.UNPROVEN, mirror.line())

    # P5 -- the destination disagreeing is a different answer from nobody looking.
    denied = prove("files", replayed(True, True), CONTRACT, denies)
    check("P5 refuted is not unproven", denied.standing is Proven.REFUTED, denied.line())

    # P6 -- a procedure that no longer runs is broken, and that is not a witness question.
    stopped = prove("files", replayed(True, False), CONTRACT, filed)
    check("P6 a replay that stopped is broken, not refuted",
          stopped.standing is Proven.BROKEN, stopped.line())

    # P7 -- and something that reported nothing proves nothing either.
    empty = prove("files", [], CONTRACT, filed)
    credulous += bool(empty)
    check("P7 no acts at all is broken", empty.standing is Proven.BROKEN, empty.line())

    print(f"\nCREDULOUS a replay nobody watched, called proven : {credulous}   (must be 0)")
    print(f"BLIND     a confirmed destination not believed   : {blind}   (must be 0)")
    print(f"FAILED    cases not matching                     : {failed}")
    return 1 if credulous or blind or failed else 0


if __name__ == "__main__":
    sys.exit(run())
