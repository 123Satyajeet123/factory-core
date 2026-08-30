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

## Result — 2026-08-30, by execution, same page and same browser

| | rung 0, direct | candidate set | has the opacity:0 checkbox |
|---|---|---|---|
| browser-use `selector_map` | — | **10 ms**, 4 candidates | **no** |
| browser-use `get_dom_tree` | — | **3 ms**, 26 nodes | yes |
| playwright `get_by_role` | **1 ms**, count=1 | — | yes |
| playwright `aria_snapshot` | — | **2 ms**, 7 lines | yes |
| playwright `locator('*')` | — | 1 ms, 17 elements | raw |

    S5  ctx.new_cdp_session(page) -> CDPSession        ok
        DOM.getDocument / querySelector / describeNode  backendNodeId 17
        DOM.resolveNode -> objectId                     ok
        Input.dispatchMouseEvent                        ok, 4 ms
    S6  Network.enable on the same session              ok
    S7  browser-use 36 runtime deps  (anthropic, google-genai, google-api-python-client,
                                      browser-use-sdk, cdp-use, bubus, posthog, ...)
        playwright   2 runtime deps  (greenlet, pyee)

**MY BLIND PREDICTION WAS WRONG, and how it was wrong is the more useful part.** I predicted
`get_dom_tree` would be an order of magnitude slower, on the evidence that a run using it
produced no output in ten minutes. It is **3 ms — faster than `selector_map`**. The stall
was a bug in my eval, and I had already written it into this gate as a vendor cost. Had the
gate been decided on the prediction it would have reached the right answer for a false
reason, which is worth less than a wrong answer honestly obtained.

**Decision: Playwright.** Not on the prediction, and not on browser-use being slow, because
it is not. On three things that were measured:

- **S3 on the common path.** Playwright resolves role and name in 1 ms with **no candidate
  fetch at all**. browser-use must build a tree every time just to match. Rung 0 is the path
  every step of every row takes.
- **S7.** Two runtime dependencies against thirty-six. browser-use brings `anthropic`,
  `google-genai`, `google-api-python-client`, an SDK and telemetry into a machine that
  never calls a model.
- **The independent bake-off.** `~/Projects/stealth/factory/BROWSER.md` measured browser-use
  failing role-and-name addressing and the painted label across five candidates. Its B4b is
  the same wall this tree hit from a different direction. Two measurements, one conclusion.

**browser-use is not disqualified and this is not a criticism of it.** `get_dom_tree`
passes S2 and S3. It is an agent framework being asked for a job it was not built for, and
the job is smaller than the framework.

**A consequence worth stating: the BROWSER machine becomes tier 1.** With browser-use the
one seam file was `bodies.py`, subclassing `BaseWatchdog`. Playwright needs no extension
point for any of it — attach, resolve, CDP, bodies are all plain documented API. The tree
now has **no vendor seam at all**, which is the shallowest tier that works, and the rule
says to take it.

**What does not change.** Actuation stays ours: Playwright refuses a covered target by
timeout, and a timeout is indistinguishable from a slow page. We keep hit-testing in the
page, dispatching over raw CDP, pacing with our own hand, and judging with our own witness.
Playwright supplies attach, resolution, candidates and bodies. It does not supply acts.

## Amendment — same day, and the reason moves a second time

Measured after the decision, before the migration:

    Accessibility.queryAXTree  checkbox 'styled checkbox'  -> 1 node, backendId 17,  8.0 ms
                               button   'target'           -> 1 node, backendId 15,  8.3 ms
                               checkbox 'boxless checkbox' -> 0 nodes,               8.4 ms
                               role=button, no name        -> 2 nodes (ambiguity visible)
    Accessibility.getFullAXTree (candidate set)            -> 13 nodes,              1.8 ms

**Raw CDP resolves role and name, and returns the `backendDOMNodeId` the guard needs.**
Playwright's `get_by_role` is faster at 1 ms and returns a handle, not a node id. Bridging a
handle to a node id means marking the element — a DOM mutation a `MutationObserver` sees —
which costs the one claim this machine's stealth rests on. A round trip to avoid that is
cheap; a mutation is not.

**So the S3 plank of the decision above is withdrawn.** Rung 0 is not 1 ms via a locator; it
is 8 ms via `queryAXTree`, and that is the honest number. This is the second time a
measurement has moved the reason for this choice, and the choice has survived both — but it
would not have survived being decided on the first reason without the second measurement.

**What the vendor is actually for, stated after measuring rather than before:** attach, a
maintained CDP transport, page and context lifecycle, and response bodies. Not resolution.
Playwright is the cheapest thing that supplies those — two runtime dependencies — and
writing a websocket CDP client with reconnection and multiplexing to avoid it would be
hand-rolling a transport.

**Ambiguity comes free.** `queryAXTree` with a role and no name returns both buttons, so
rung 0's refusal on two-plus is the platform's answer rather than our arithmetic.
