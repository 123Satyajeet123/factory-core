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
