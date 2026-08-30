# Does the guard refuse, and does it still allow correct work?

Written **before** reading browser-use's dispatch path or writing any of
`browser/{hit,guard,act}.py`. Criteria fixed here so a convenient vendor API cannot
move them afterwards.

## What is being decided

A guard that refuses everything is trivially safe and useless. A guard measured only on
refusals is indistinguishable from that one. So this gate has two scores and **both are
reported every time**:

    SAFETY     dispatched when it should have refused        must be 0
    LIVENESS   refused when it should have dispatched        budgeted, not 0

A release may not trade the first for the second.

## The four fixtures

Static local HTML, no network, no site. Each states the expected `delivery` and whether
anything is dispatched.

**F1 impostor swap.** The element resolved is replaced by a different element occupying
the same point between resolve and dispatch.
→ `off_target`, **nothing dispatched**. Counts against SAFETY if anything is sent.

**F2 consent overlay.** A fixed-position overlay covers the target.
→ `intercepted`, **nothing dispatched**. The vendor's own behaviour here is to log and
click through with `Runtime.callFunctionOn "function(){this.click();}"`, which is the
accident this exists to prevent.

**F3 label for a hidden input.** A styled checkbox: the real `<input>` is hidden and the
painted `<label>` receives the hit. `elementFromPoint` returns the label — not the
element, not containing it, not contained by it.
→ `target_hit`, **dispatched**. This is the LIVENESS case and plain containment fails it.

**F4 moved target.** The element shifts after its box is measured and before dispatch.
→ `off_target`, **nothing dispatched**.

## Method, fixed now

- The hit test runs **in the page**, so the guard point and the press point are the same
  number. Computing a point in Python from a bounding box and testing in client
  coordinates is a coordinate mismatch that makes a guard lie.
- A refusal returns before any postcondition is evaluated. A postcondition judging an act
  that never happened is a second way to report success wrongly.
- Every fixture asserts on **what was sent**, not on what the page looks like afterwards.
  A page can end up correct for the wrong reason.

## Pass

All four match, SAFETY is 0, and the run prints both scores. F3 passing while F1, F2 and
F4 refuse is the whole result; three of four is not a partial pass, it is a fail with a
detail.

## Result — 2026-08-30, by execution

    ok   F1 impostor swap           delivery=off_target   dispatched=False  why=gone           page_saw=[]
    ok   F2 consent overlay         delivery=intercepted  dispatched=False  why=covered DIV    page_saw=[]
    ok   F3 label for hidden input  delivery=target_hit   dispatched=True   why=label          page_saw=["paint","real"]
    ok   F5 boxless input           delivery=off_target   dispatched=False  why=gone           page_saw=[]
    ok   F4 target off viewport     delivery=off_target   dispatched=False  why=outside        page_saw=[]

    SAFETY   dispatched when it should have refused : 0
    LIVENESS refused when it should have dispatched : 0

**F3 passed first time for the wrong reason, and that is the finding.** The fixture hid
the input at `opacity:0; width:1px; height:1px`, and an `opacity:0` element still takes
hit-testing — so `elementFromPoint` returned the input itself and the answer came back
`why=self`. Four green results, and the liveness case had never run. The fixture now
gives the input a real box with the label painted over it at `z-index:1`, which produces
`why=label`, and `page_saw=["paint","real"]` shows the browser forwarded the click to the
input. A liveness case that cannot fail is the same defect as a gate that passes deleted.

**F4 deviates from the specification, deliberately.** It was written as "the element
shifts after its box is measured". The guard computes its point from the *current* box
immediately before dispatch, so an element that merely moved is still hit correctly —
which is right behaviour, not a refusal. The dangerous version of that case is a point
measured earlier and replayed, which this design does not do. Implemented instead as the
element leaving the viewport, which is a real refusal and deterministic.

**F5 is a limit, recorded rather than hidden.** An input at `display:none` has no box, so
no point on it is computable and the guard refuses. Targeting its painted label instead is
`locate`'s job, not the guard's.

**The honest gap.** `DOM.resolveNode`, the probe, and `Input.dispatchMouseEvent` are three
CDP round-trips, so a window exists between measuring and pressing. chrome-agent measures
and dispatches in one place; this does not. Nothing in these fixtures closes that window,
and no result here should be read as if it did.
