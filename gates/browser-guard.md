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

## Result

(filled in by execution — not by reasoning)
