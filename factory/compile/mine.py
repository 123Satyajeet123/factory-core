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

from typing import Any

from factory.core.contract import Contract

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
    print(f"mine: changed -> {changed.expects} identifies={changed.identifies!r}; "
          f"keyed identifies={keyed.identifies!r}; no-op -> {{}}")


if __name__ == "__main__":
    _self_check()


def irreversible(mining: Any) -> bool:
    """Whether the compiler judged this effect impossible to undo.

    Theirs, not ours. `Effect.risk` is assessed at compile time from the demonstration, and
    `needs_operator_confirmation` is their flag for an effect a person should see first.
    Re-deciding it here would be a second mechanism, and ours would be a list of verbs.
    """
    return any(getattr(effect, "risk", "") == "irreversible"
               or getattr(effect, "needs_operator_confirmation", False)
               for effect in getattr(mining, "effects", ()) or ())
