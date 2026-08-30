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

from pydantic import BaseModel

from factory.compile.mine import contract_of, events, mined, shown_reversible
from factory.core.contract import Contract
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
            name=act.target.name if act.target else None,
            #: Which surface, in the field that already means it. Their world calls it a
            #: window; a browser calls it a tab, and both are "not the one you are on".
            window_name=act.surface or None),
    )


def _their_step(act: Act, index: int = 0, intent: str = "") -> Any | None:
    """One act, in the shape their compiler consumes. None for a doing they have no word for.

    ONE BUILDER, TWO CALLERS. Alignment and effect mining both hand the vendor a step, and
    they must hand it the SAME step: a contract derived against a step the aligner never
    saw would be a check on something that was not compiled.
    """
    from openadapt_flow.ir import ActionKind
    from openadapt_flow.ir import Step as TheirStep

    kind = AS_ACTION.get(act.doing)
    if kind is None:
        return None
    return TheirStep(id=f"a{index}", intent=intent or act.doing.value,
                     action=ActionKind[kind], text=act.value or None, anchor=_anchor(act))


def as_trace(segment: Segment, name: str) -> Any:
    """One demonstration, in the shape their compiler consumes."""
    from openadapt_flow.ir import Workflow as TheirWorkflow

    steps = [built for index, act in enumerate(segment.acts)
             if (built := _their_step(act, index, segment.intent)) is not None]
    return TheirWorkflow(name=name, steps=steps)


class Induced(BaseModel):
    """What came of aligning some demonstrations: a program, or what stopped one.

    A workflow is emitted only when nothing was left undecided. The compiler refuses on a
    divergence it cannot explain and asks instead -- and an empty `workflow` with the
    questions thrown away is indistinguishable from a program that does nothing.
    """

    workflow: Workflow | None = None
    questions: tuple[str, ...] = ()

    def __bool__(self) -> bool:
        return self.workflow is not None


def contract_for(step: Step, shown: list[Segment]) -> Contract | None:
    """What must be true after this step, derived from the acts it was induced from.

    MATCHED THE WAY `binds_row` MATCHES, on doing and target. A second way of joining a
    step back to the acts behind it would be a second mechanism, and the two would disagree
    the first time either end grew a field -- silently, as a contract checking a step that
    was compiled from somewhere else.

    THE FIRST DEMONSTRATION THAT DERIVED ONE WINS, and that is safe because `binds_row`
    runs after: whichever demonstration's value got bound, the field that varies is pointed
    at its parameter rather than at that value.

    NONE IS AN ANSWER. A step whose acts changed nothing observable gets no contract, and
    `witness/coverage` counts it as demand rather than something papering over it as
    checked. Filling one in to raise the number is the failure this whole path avoids.
    """
    for _, mining in _minings(step, shown):
        got = contract_of(mining)
        if got.expects:
            return got
    return None


def _minings(step: Step, shown: list[Segment]) -> list[tuple[Act, Any]]:
    """The vendor's mining of every act this step was induced from, in order."""
    found = []
    for segment in shown:
        around = events(segment.acts, segment.after)
        for index, (act, event) in enumerate(zip(segment.acts, around, strict=True)):
            if act.doing is not step.doing or act.target != step.target:
                continue
            their = _their_step(act, index, segment.intent)
            if their is not None:
                found.append((act, mined(event, their)))
    return found


def findable(step: Step, shown: list[Segment]) -> bool:
    """Can the control this step names be told apart from its siblings on that page?

    ASKED OF THE RECORD, NOT OF A PAGE. `Act.among` is what the page was offering when the
    person acted, described by the same function `locate` describes candidates with on
    replay, so this is the answer `locate.settle` will give -- computed now, while somebody
    is still there to answer it.

    THE ORDINARY CASE IS A TABLE. Every row's control carries the same role and the same
    name, a person picks one by where it sits, and `locate` refuses on two matches. Without
    this the demonstration compiles clean and the step refuses on the first real run.

    ONE DEMONSTRATION SEEING IT UNIQUELY IS NOT ENOUGH: if any demonstration saw siblings,
    the page has them, and the run that meets them is the one that matters.
    """
    seen = [act for act, _ in _minings(step, shown)]
    return bool(seen) and not any(act.ambiguous for act in seen)


def consequential(step: Step, shown: list[Segment]) -> bool:
    """Whether a person has to allow this step before it runs.

    NOT A LIST OF VERBS, WHICH IS WHY THIS IS DERIVED AND NOT WRITTEN. A verb list does not
    know that one press sends and the next saves a draft, and it would be per-destination
    knowledge in a driver -- the thing `evals/agnostic` exists to refuse.

    ONE DEMONSTRATION SHOWING IT REVERSIBLE IS ENOUGH. Whether an act can be taken back is
    a property of the act, not of the afternoon: if any demonstration observed the effect
    land somewhere readable, the step is one the system can check and undo reasoning about.
    Everything else asks.
    """
    return not any(shown_reversible(mining) for _, mining in _minings(step, shown))


def with_contracts(workflow: Workflow, shown: list[Segment]) -> Workflow:
    """The same program, with every step told what to expect after it and what it costs.

    IRREVERSIBILITY IS SET HERE FOR THE SAME REASON THE CONTRACT IS. `Step.irreversible`
    is what `run/harness.py` checks before an act reaches the driver, and nothing set it:
    a compiled send was indistinguishable from a compiled save, so the permit gate was a
    branch that could not be taken.

    ATTACHED HERE, NOT BY A CALLER. `contract_of` had no caller outside its own self-check
    for as long as this function did not exist, so every compiled workflow reached the
    harness with `contract=None` and the witness -- the whole point of the system -- never
    ran on real work. A composition root that has to remember is a composition root that
    forgets.
    """
    told = []
    for step in workflow.steps:
        contract = contract_for(step, shown)
        changed: dict[str, Any] = {"irreversible": consequential(step, shown)}
        if contract is not None:
            changed["contract"] = binds_row(contract, workflow, shown)
        told.append(step.model_copy(update=changed))
    return workflow.model_copy(update={"steps": told})


def unrepresentable(induced: Any) -> tuple[str, ...]:
    graph = getattr(induced, "program", None)
    asked = []
    for state in (getattr(graph, "states", None) or {}).values():
        if getattr(state, "step", None) is not None:
            continue
        carried = next((kind for kind in ("loop", "decision", "subflow")
                        if getattr(state, kind, None) is not None), "")
        if carried:
            body = getattr(getattr(state, carried), "body", "") or carried
            asked.append(f"{state.id} is a {carried} over {body!r} and this compiler has no "
                         f"shape for one. Its steps are not in the graph, so emitting the "
                         f"rest would be a program that runs clean and does part of the task.")
    return tuple(asked)


def program(segments: list[Segment], name: str) -> Induced:
    """Demonstrations in, a program or a refusal out."""
    got = induce(segments)
    asked = tuple(
        getattr(getattr(u, "question", None), "prompt", None) or getattr(u, "detail", "")
        for u in (getattr(got, "uncertainties", None) or []))
    asked += unrepresentable(got)
    if asked:
        return Induced(questions=asked)
    shown = [segment for segment in segments if segment.by_person()]
    return Induced(workflow=with_contracts(workflow_of(got, name), shown))


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
        #: THE GUARD IS THE ANSWER, NOT NOISE. An act seen in one demonstration and not
        #: another comes back with `on_unmet='skip'`; dropping it made an aside mandatory.
        guard = getattr(their, "guard", None)
        steps.append(Step(
            doing=doing, intent=their.intent or "",
            target=Target(role=(where.role or "") if where else "",
                          name=(where.name or "") if where else ""),
            value=their.text or "", param=their.param or "",
            surface=(where.window_name or "") if where else "",
            optional=getattr(guard, "on_unmet", None) == "skip"))
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
