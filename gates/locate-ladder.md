# When role and name find nothing, what answers next?

Written **before** reading any candidate. Criteria and a blind prediction are fixed here so
that what happens next is a test rather than a story told afterwards.

## What is broken

`locate` has one rung. Measured on an eleven-element fixture, the vendor's serialisation
offers four, and the `<input>` behind a painted label is not among them:

    BUTTON role=button    name='target'
    LABEL  role=LabelText name=''
    LABEL  role=LabelText name=''
    BUTTON role=button    name='skittish'

A control a person clicks without thinking cannot be addressed. The rung returns `no match`
and the driver stops. There is no second channel and no question.

## Candidates, all of them, named now so that dropping one is visible

1. **browser-use's unfiltered DOM tree** — the vendor we already have. `selector_map` is a
   filtered view; the tree behind it is not.
2. **CDP `Accessibility.getFullAXTree`** — the platform itself, no vendor.
3. **Playwright's locator engine** (`get_by_role`) — a second vendor's resolver, usable
   over the same CDP endpoint.
4. **A vision model on a screenshot** — the expensive rung.
5. **The question rail** — ask, once, and keep the answer.

## Criteria

**L1 coverage.** On the fixture, does the rung reach the styled checkbox that role and name
missed? Reported per rung, not as a total.

**L2 no site knowledge.** A rung may not need a selector, an XPath or a host table written
by us. Per-destination knowledge enters through a question and is stored on the workflow,
never as a lookup in library code — that rule is what keeps this working on the next
destination.

**L3 refuses on ambiguity, at every rung.** Zero or two-plus is a refusal, not a first
match. A cheaper rung is not allowed to be sloppier.

**L4 the answer says which rung produced it.** Evidence must record how a control was
found, or a cheap wrong answer is indistinguishable from an expensive right one, and
nothing downstream can learn which rung is worth running.

**L5 ordered by cost, and only descends on a miss.** A rung runs only when the one above it
found nothing. Order by truth is fixed; this order is by cost, so it is a starting order to
be scored on outcomes rather than a fact.

**L6 the bottom is a question, not a None.** When every rung misses, the result is a
Question — which is the mechanism by which this system learns a destination at all.

## Blind prediction

- Rung 2 **will** find the checkbox: the input is in the DOM with a label association, so
  what dropped it is the vendor's interactive FILTER, not the platform. If this is wrong
  and the platform also lacks it, the whole ladder premise is weaker than assumed.
- The `display:none` checkbox will remain unreachable at every rung except asking, and that
  is correct rather than a gap — it has no box, and the thing to press is its label.
- Playwright's engine will overlap rung 2 heavily and add a second actuator's worth of
  dependency for little coverage. Predicted to be dropped on cost, not on quality.

## What would make this dishonest

Adding a rung that works by knowing this fixture. A rung that needs `#real` written down
has not solved anything; it has moved the problem into our source.

## Result

(filled in by execution — not by reasoning)

## Amendment — 2026-08-30, before any code, and the original above is left standing

**The candidate list was wrong, and wrong in a way worth keeping visible.** Candidates 1, 2
and 3 — the vendor's unfiltered tree, the platform's AX tree, Playwright's engine — are the
same candidate three times: *another structural channel*. Ordering them is a hardcoded
sequence of addressing strategies, and that list never closes. A canvas cell, a drag
handle, a chart region, a virtualised row that does not exist until something scrolls: each
would want a fourth entry, then a fifth.

**What identifies a target is the evidence from the demonstration, not a strategy.** The
person's act was recorded, along with what the page did afterwards. Locate's job is to find
the thing that matches that evidence now. There are not N strategies; there is one job with
a widening set of candidate sources.

So the rungs are:

    0  structural match against the recorded evidence          free
    1  the MODEL chooses among candidates, given what was
       recorded and what the page offers now                   a model call
    2  pixels, when the page offers no structure at all        a vision call
    3  ask, once, and the answer is stored on the workflow     a person

Rung 1 is not "try another selector". It is the model deciding which of the things on this
page is the thing that was demonstrated — the one part of this that is not plumbing.

**Two consequences that were not in the original.**

*The witness does not need the control.* On a canvas grid a cell may never be addressable,
and the effect of acting on it is still confirmable on a channel that did not act. An
unaddressable control is not an unverifiable act, which is why locate and witness are
separate machines rather than one perception layer.

*Resolution is memory, and this is where the cost goes back down.* Rung 1 costs a model
call the first time. Once it resolves and a witness confirms, the resolution is stored
against that step and rung 0 answers on every later run. The promotion is earned by a
receipt, never by the model's own confidence.

**L1 is amended accordingly.** Coverage is still reported per rung, but "does rung 2 find
the checkbox" is no longer the question — rung 2 is now pixels. The question for the
structural rung is whether the evidence recorded at demonstration time is enough to find
the control again, and where it is not, whether the descent happens rather than the driver
stopping.

**The blind prediction stands and is now testable in a different place**: the input is in
the DOM with a label association, so what dropped it is the vendor's interactive filter and
not the platform. That is a question about the candidate SET, which rung 0 and rung 1 share.
