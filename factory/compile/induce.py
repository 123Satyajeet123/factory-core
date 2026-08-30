"""Several demonstrations of one task, aligned into a program.

THEIRS, NOT OURS. `openadapt_flow.compiler.induction.induce_program` is deterministic and
model-free at its core -- align, then parameters, loops, branches, optional steps. It
quarantines rather than emitting when intent stays underdetermined, which is the same
refusal this project makes everywhere else, arrived at independently.

THE IMPEDANCE, STATED. Their `Anchor` was built for desktop recordings: `template`,
`region` and `click_point` are required, because a screenshot crop is how that world finds
a control again. We find controls by role and name from the accessibility tree, and their
`StructuralLocator` carries exactly those two.

So the adapter answers honestly rather than plausibly. `template` is empty because we hold
no image. `region` and `click_point` are what was observed at the moment of the act. None
of it is ever used to aim -- `browser/locate.py` resolves by role and name, and aiming by a
recorded coordinate is the failure that rule exists to prevent.
"""

from __future__ import annotations

from typing import Any

from factory.core.ledger import Act, Segment
from factory.core.verbs import Doing
from factory.core.workflow import Step, Target, Workflow

#: Our vocabulary to theirs. A doing with no entry is one their compiler has no word for,
#: and is dropped with the segment saying so rather than mapped onto something close.
AS_ACTION = {Doing.PRESS: "CLICK", Doing.WRITE: "TYPE", Doing.GO: "NAVIGATE"}


def _anchor(act: Act) -> Any:
    from openadapt_flow.ir import Anchor, StructuralLocator

    left, top, right, bottom = act.box or (0, 0, 0, 0)
    x, y = act.where or (0, 0)
    return Anchor(
        template="",
        region=(int(left), int(top), int(right - left), int(bottom - top)),
        click_point=(int(x), int(y)),
        structural=StructuralLocator(
            role=act.target.role if act.target else None,
            name=act.target.name if act.target else None),
    )


def as_trace(segment: Segment, name: str) -> Any:
    """One demonstration, in the shape their compiler consumes."""
    from openadapt_flow.ir import ActionKind
    from openadapt_flow.ir import Step as TheirStep
    from openadapt_flow.ir import Workflow as TheirWorkflow

    steps = []
    for index, act in enumerate(segment.acts):
        kind = AS_ACTION.get(act.doing)
        if kind is None:
            continue
        steps.append(TheirStep(
            id=f"a{index}", intent=segment.intent or act.doing.value,
            action=ActionKind[kind], text=act.value or None, anchor=_anchor(act)))
    return TheirWorkflow(name=name, steps=steps)


def induce(segments: list[Segment]) -> Any:
    """Align demonstrations of the same task. Two or more; one is the degenerate case.

    Only segments a PERSON drove are admissible. Inducing from the factory's own replays
    would teach the compiler what we already do, which is not a demonstration of anything.
    """
    from openadapt_flow.compiler.induction import induce_program

    shown = [s for s in segments if s.by_person()]
    return induce_program([as_trace(s, f"t{i}") for i, s in enumerate(shown)])


#: Theirs back to ours. The compiler emits its own vocabulary and this is the one place
#: that translates it, so a member they add shows up here as a KeyError rather than as a
#: step that silently does nothing.
AS_DOING = {"click": Doing.PRESS, "type": Doing.WRITE, "navigate": Doing.GO}


def _in_order(graph: Any, states: dict[str, Any]) -> list[Any]:
    """Follow the graph from its entry.

    THE STATES ARE A DICT AND A DICT IS NOT AN ORDER. Iterating `.values()` emitted press,
    press, write for a demonstration that typed before it saved -- so the run pressed Save
    on an empty field and then typed into nothing. Measured, and it ran clean.
    """
    seen, walk, at = [], set(), getattr(graph, "entry", None)
    while at and at in states and at not in walk:
        walk.add(at)
        state = states[at]
        seen.append(state)
        following = getattr(state, "transitions", None) or []
        at = next((getattr(t, "to", None) or getattr(t, "target", None)
                   for t in following), None)
    return seen or list(states.values())


def workflow_of(induced: Any, name: str) -> Workflow:
    """The induced program, as the thing `run/harness.py` executes.

    THE STEPS ARE IN `program.states`, NOT IN `result.workflow`. Measured: a run that
    induced a parameter correctly returned a `workflow` carrying zero steps, and reading
    that field would have produced an empty program that ran clean and did nothing.
    """
    graph = getattr(induced, "program", None)
    states = getattr(graph, "states", None) or {}
    steps: list[Step] = []
    for state in _in_order(graph, states):
        their = getattr(state, "step", None)
        if their is None:
            continue
        doing = AS_DOING.get(their.action.value)
        if doing is None:
            continue
        where = their.anchor.structural if their.anchor else None
        steps.append(Step(
            doing=doing, intent=their.intent or "",
            target=Target(role=(where.role or "") if where else "",
                          name=(where.name or "") if where else ""),
            value=their.text or "", param=their.param or ""))
    return Workflow(name=name, steps=steps,
                    params=tuple(getattr(induced, "param_specs", {}) or ()))


def binds_row(contract: Any, workflow: Workflow, shown: list[Segment]) -> Any:
    """Point a contract's fields at the parameters whose values belong in them.

    A contract is derived from ONE demonstration and holds that demonstration's value. Which
    parameter that value came from is answered by looking at what the varying step actually
    took across every demonstration -- not by `param_specs.example`, which holds the first
    trace's value while the contract may have come from the second. Measured: they did not
    match, `varies` stayed empty, and every row confirmed against the demonstrated record.
    """
    demonstrated: dict[str, set[str]] = {}
    for step in workflow.steps:
        if not step.param or step.target is None:
            continue
        seen = demonstrated.setdefault(step.param, set())
        for segment in shown:
            seen.update(act.value for act in segment.acts
                        if act.doing is step.doing and act.target == step.target
                        and act.value)

    varies = {field: param
              for field, value in contract.expects.items()
              for param, values in demonstrated.items() if value in values}
    return contract.model_copy(update={"varies": varies}) if varies else contract
