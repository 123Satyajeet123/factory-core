# What do we still take from a browser vendor?

Written **before** measuring, and this is a RE-decision rather than a first one, so what is
already known is stated up front rather than discovered conveniently later.

## Why this is being re-opened

browser-use was adopted on my reading. A five-candidate bake-off run independently
(`~/Projects/stealth/factory/BROWSER.md`, real Chrome, no models) measured it failing role
and name addressing, failing the painted label, and clicking through occlusion by design —
and chose Playwright. Its B4b failure is the same wall this tree hit from a different
direction, twice measured, so it is a fact rather than an opinion.

## The question is narrower than theirs, and that is the point

We do not use a vendor's click, its locator timeouts, its hit test, its pacing or its
verdict. We dispatch CDP ourselves, hit-test in the page, pace with our own hand, and judge
with our own witness. So the question is not "which is the better browser library". It is:

> Given that we act, guard, pace and witness ourselves, what is left that we take — and
> which vendor supplies exactly that, cheapest?

What is plausibly left: **attach**, **a candidate set**, **response bodies**, and **a raw
CDP client we are not fenced away from**.

## What is already established, so it is not re-litigated

- browser-use `selector_map` omits a control carrying the exact role and name being
  searched for, because the input is painted at `opacity:0`. Measured here and there.
- browser-use `DomService.get_dom_tree` DOES carry it, with role, name and a box. So
  "cannot" is too strong; the filter was the problem, not the platform.
- Playwright refuses a covered target by TIMEOUT. A timeout is indistinguishable from a
  slow page, which is one exception meaning three things. We need a typed refusal, and we
  already have one.
- pydoll's `stop()` terminated a browser it had only attached to. Disqualifying for a
  machine whose premise is the person's own browser.
- Per-op: browser-use 0.4ms, playwright 9.6ms, over 50 operations.

## Criteria

**S1 attach, and add no tells.** Connects to a browser already running; its own launch path
is never used. All five candidates already passed this; it is here because a regression
would be silent.

**S2 the candidate set is complete.** Hands over every element that has a box — including
one painted at `opacity:0` whose label is what the person sees. Anything less cannot be
chosen from, at any rung.

**S3 what one candidate-set fetch COSTS, on the same page.** This is the criterion this
gate exists for, and it is unmeasured. It is paid on every step of every row of every run,
so a difference here outweighs a per-operation difference by orders of magnitude.

**S4 nothing we have rejected is forced on us.** Using it for candidates must not oblige us
to use its actuation, its timeouts or its occlusion behaviour.

**S5 the CDP client stays reachable.** We dispatch, hit-test and collect bodies over raw
CDP. A vendor that fences it off cannot be used at all.

**S6 response bodies on the same connection**, without a second attach.

**S7 what it drags in.** Weight, and whether it brings a model client, telemetry, or an
agent loop we do not want.

## Blind prediction

**S3 decides this, and browser-use loses it.** `DomService` carries its own TODO — *"we
start a new websocket connection PER STEP"* — and a run that completed seven cases in about
two minutes on `selector_map` produced no case output in ten on `get_dom_tree`. I expect
Playwright's snapshot to be an order of magnitude cheaper, and I expect its 9.6ms per
operation to be irrelevant beside it.

If that is wrong and the two are comparable, browser-use keeps the spine on S2 plus S9's
per-op speed, and this gate will have cost one measurement to confirm the incumbent.

## Decision rule, fixed now

- S2 and S5 are pass/fail. A candidate failing either is out regardless of speed.
- S3 decides between candidates that pass. A slower fetch is only acceptable if it is the
  only one that passes S2.
- Adopt for the narrow job, never wholesale. Whatever is chosen supplies attach, candidates
  and bodies; it does not get to supply actuation.
- If the incumbent wins, say so plainly and record that the gate cost a measurement.

## Result

(filled in by execution — not by reasoning)
