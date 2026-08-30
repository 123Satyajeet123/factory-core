"""A contract derived from what the demonstration SAW CHANGE.

WHY THIS EXISTS AT ALL. A contract binding what merely exists can only ever be checked for
existence: a record that was already there confirms, and CONFIRMED then means "present"
rather than "this act caused it". Binding the delta is the whole fix, and it belongs here
because the delta is in the demonstration, not in the reading.

A VIEW OVER THE VENDOR, NOT A SECOND MINER. `openadapt_flow.compiler.effect_mining` already
turns a recorded before/after into effects, in a precedence its own docstring states:
an observed system-of-record delta first, a DOM field map next, an on-screen read-back
next, a flagged placeholder for a consequential act, and no effect last with a reason.
Deriving the same thing again here would be two mechanisms for one job.

REFUSING IS AN OUTPUT. `disposition` is theirs and it is the honest one: anything but
`derived` yields an empty contract, which `witness/judge` answers UNVERIFIABLE and
`witness/coverage` counts as demand. Filling one in to raise the number is the failure this
is built to avoid.

NO MODEL IS ON THIS PATH. The procedure and the check both come from the record.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from factory.core.contract import Contract
from factory.core.ledger import Act

#: The vendor says a real derivation happened. Every other value carries a reason instead.
DERIVED = "derived"


def mined(event: dict[str, Any], step: Any) -> Any:
    """The vendor's mining of one demonstrated step. Callers do not import it themselves."""
    from openadapt_flow.compiler.effect_mining import mine_step_effects

    return mine_step_effects(event, step)


def contract_of(mining: Any) -> Contract:
    """What must be true afterwards, as fields, or nothing.

    A form field that took a value is not a record write -- the vendor flags that with
    `needs_operator_confirmation`, and binding it anyway would confirm typing rather than
    the thing the typing was for.
    """
    if getattr(mining, "disposition", "") != DERIVED:
        return Contract()

    expects: dict[str, str] = {}
    identifies = ""
    for effect in mining.effects:
        if getattr(effect, "needs_operator_confirmation", False):
            continue
        for field, value in (getattr(effect, "match", None) or {}).items():
            expects[str(field)] = str(value)
        field, value = getattr(effect, "field", None), getattr(effect, "value", None)
        if field and value is not None:
            expects[str(field)] = str(value)
        #: Observed, never assumed. The vendor populates this only when the destination
        #: actually issued a key the demonstration saw.
        for bound, want in expects.items():
            if want == getattr(effect, "idempotency_key", None):
                identifies = bound
    return Contract(expects=expects, identifies=identifies)


def events(acts: Sequence[Act], after: Sequence[Any] = ()) -> list[dict[str, Any]]:
    """The before and after around every act, from what the page fetched between them.

    NO SNAPSHOT MECHANISM, AND THAT IS THE POINT. A "before/after" reads like something
    somebody has to go and take. It is not: `Act.saw` already carries what the page had
    fetched when the act happened, so the record set as of act N is everything seen through
    act N, and the record set after it is everything seen through act N+1. The delta the
    vendor mines is the gap between two consecutive acts, and nothing had to snapshot
    anything.

    CUMULATIVE, NEVER THE LATEST RESPONSE ALONE. An app that answers a write with only the
    written record, and an app that re-lists everything, must produce the same delta. Taking
    the last response as the whole state would read the first as though every other record
    had been deleted.

    THE LAST ACT NEEDS `after`. A demonstration ends on the act that mattered and its
    effect arrives afterwards, so without what was fetched at the moment recording stopped
    the final save binds nothing. `Segment.after` is where that is kept.

    THE SAME EXTRACTOR THE READER USES. `Exchange.records` is what `witness/readers` asks,
    so a contract can only ever bind fields some reader can address -- a field bound here
    and unreadable there would come back as blindness rather than as the bug it is.
    """
    if not acts:
        return []
    windows: list[dict[str, Any]] = [{} for _ in acts]
    for surface in {act.surface for act in acts}:
        theirs = [index for index, act in enumerate(acts) if act.surface == surface]
        seen: list[dict[str, str]] = []
        through: list[list[dict[str, str]]] = []
        for index in theirs:
            seen = seen + [row for e in acts[index].saw for row in e.records()]
            through.append(seen)
        through.append(seen + [row for e in after if e.url.startswith(surface or "\0")
                               for row in e.records()])
        for place, index in enumerate(theirs):
            windows[index] = {"sor_before": through[place], "sor_after": through[place + 1]}
    return windows


def why_not(mining: Any) -> str:
    """Why no contract could be derived. Empty when one was."""
    return "" if getattr(mining, "disposition", "") == DERIVED else getattr(mining, "reason", "")


def _self_check() -> None:
    """C1 and C3, against the vendor. No browser.

        uv run python -m factory.compile.mine
    """
    from openadapt_flow.ir import ActionKind
    from openadapt_flow.ir import Step as TheirStep

    step = TheirStep(id="s1", intent="write the row", action=ActionKind.TYPE,
                     text="Ada Lovelace")
    before = [{"id": "883973", "name": ""}]
    after = [*before, {"id": "883974", "name": "Ada Lovelace"}]

    changed = contract_of(mined({"sor_before": before, "sor_after": after}, step))
    assert changed.expects == {"name": "Ada Lovelace"}, changed.expects
    assert not changed.identifies, "nothing here proves this act caused it"

    #: The same write, where the destination issued a key. Presence of THAT record is
    #: causation, because the key exists only because we wrote it.
    keyed = contract_of(mined(
        {"sor_before": before,
         "sor_after": [*before, {"id": "883974", "name": "Ada Lovelace", "key": "run-7f3a"}]},
        step))
    assert keyed.identifies == "key", keyed
    assert keyed.expects["key"] == "run-7f3a"

    #: C1. The same snapshot twice is a no-op, and a no-op binds nothing however
    #: consequential the step looked.
    still = mined({"sor_before": before, "sor_after": before}, step)
    assert contract_of(still).expects == {}, "C1 a no-op must bind nothing"
    assert why_not(still), "C3 and it must say why"

    #: A form field taking a value is not a record write.
    typed = mined({"dom_fields_before": {"name": ""},
                   "dom_fields_after": {"name": "Ada Lovelace"}}, step)
    assert contract_of(typed).expects == {}, "typing is not the thing the typing was for"

    nothing = mined({}, step)
    assert contract_of(nothing).expects == {} and why_not(nothing)

    #: The same contract, derived from two consecutive ACTS rather than a hand-built
    #: before/after. Nothing snapshots anything: the write's response lands on the act
    #: that follows it, which is what makes the gap the effect.
    from factory.core.evidence import Exchange
    from factory.core.ledger import Act
    from factory.core.verbs import Doing

    def answered(body: str) -> Exchange:
        return Exchange(url="", status=200, content_type="application/json", body=body)

    listed = answered('[{"id": "883973", "name": ""}]')
    written = answered('[{"id": "883973", "name": ""},'
                       ' {"id": "883974", "name": "Ada Lovelace"}]')
    demonstrated = [
        Act(doing=Doing.WRITE, value="Ada Lovelace", saw=[listed]),
        Act(doing=Doing.PRESS, saw=[written]),
    ]
    around = events(demonstrated)
    assert len(around) == len(demonstrated), "one before/after per act"
    from_acts = contract_of(mined(around[0], step))
    assert from_acts.expects == changed.expects, (from_acts.expects, changed.expects)

    elsewhere = [
        Act(doing=Doing.PRESS, surface="http://one", saw=[]),
        Act(doing=Doing.PRESS, surface="http://two", saw=[written]),
        Act(doing=Doing.PRESS, surface="http://one", saw=[answered('[{"a": "1"}]')]),
    ]
    split = events(elsewhere)
    crossed = [row for row in split[0]["sor_after"] if row.get("name") == "Ada Lovelace"]
    assert not crossed, (
        "an act's effect is what arrived on ITS OWN surface before the next act there. "
        "Taking the next act in the list attributes another destination's records to it, "
        "and the run CONFIRMS a step against something it did not cause.")
    assert split[0]["sor_after"] == [{"a": "1"}], split[0]["sor_after"]
    assert contract_of(mined(split[1], step)).expects == {}, (
        "and the act on the other surface keeps its own window too")

    #: A demonstration that recorded no traffic binds nothing, and says so. This is the
    #: state every demonstration was in before `Act.saw` existed.
    blind = events([Act(doing=Doing.PRESS), Act(doing=Doing.PRESS)])
    assert contract_of(mined(blind[0], step)).expects == {}, "no evidence, no contract"
    assert why_not(mined(blind[0], step)), "and it must say why"

    print(f"mine: changed -> {changed.expects} identifies={changed.identifies!r}; "
          f"keyed identifies={keyed.identifies!r}; no-op -> {{}}; "
          f"from two acts -> {from_acts.expects}; "
          f"another surface's records are not this act's effect")


if __name__ == "__main__":
    _self_check()


def shown_reversible(mining: Any) -> bool:
    """Did the demonstration SHOW this effect being one that can be taken back?

    NOT `Effect.risk` ASKED OF THE VENDOR. Their miner READS `step.risk` off the step it is
    handed -- `effect_mining.py:644` and `:677` -- and never derives it, so a predicate over
    that field is a predicate over a value we would have had to supply. It was one: nothing
    in this tree set it, so the check returned False for every step and the permit gate in
    `run/harness.py` was a branch that could not be taken. A guard that always answers one
    way passes every test written in that direction.

    WHAT THEY DO DERIVE IS THE EFFECT. A record write observed in a system-of-record delta
    comes back `reversible`, and that IS evidence: the demonstration watched the value
    appear somewhere it can be read again.

    UNKNOWN IS NOT REVERSIBLE, and that is the whole safety of it. A step whose consequence
    left the surface -- a send, a submit, a payment -- has no effect anybody observed, so
    nothing here reassures the caller and a person is asked instead. The opposite default
    is a system that mails a hundred strangers because no reader happened to be admitted.
    """
    effects = getattr(mining, "effects", ()) or ()
    if getattr(mining, "disposition", "") != DERIVED or not effects:
        return False
    return all(getattr(effect, "risk", "") == "reversible"
               and not getattr(effect, "needs_operator_confirmation", False)
               for effect in effects)
