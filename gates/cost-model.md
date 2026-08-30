# What does a step cost, and in what unit?

Written after two versions of `observe.py` existed and before a third. Neither was decided
on its merits — each replaced the other because it was written later, which is not a reason.

## What is wrong with what is there

**A hand-assigned category table is a number that was picked.** `PRICED` maps each rung to
one of four names. `gates/promotion-threshold.md` rejected exactly this shape for the memory
threshold — *"both numbers would have been picked rather than derived"* — and the objection
does not weaken because the numbers here are words.

**`free` sums FREE and QUERY.** A CDP round trip is not free. Lumping them means the
ordering between them carries no weight in any number the system reports, so the distinction
exists only in the enum.

**`reasoned` sums MODEL and PERSON, and this is the damaging one.** A person is not an
expensive model. They are slower by orders of magnitude, they may not answer at all, and
"this workflow stopped needing a person" is the single largest thing this system could ever
report. Summed into one number it is invisible — a run that traded a person for three model
calls looks worse, and it is enormously better.

## What is already measured, and it is not a category

    playwright per-op            9.6 ms      gates/browser-spine.md
    one guarded act            1116 ms       door_eval
    the door's wire               3 ms       door_eval
    a kernel round trip           0.3 ms     gates/kernel-isolation.md
    rung 0                        1 ms       cheaper_eval

This repository already reasons in milliseconds everywhere. The unit exists; only the model
was invented.

## Criteria

**X1 one unit, and it is observed.** Seconds. A rung's cost is the median of what that rung
actually took, accumulated across runs — not a name somebody assigned it. A cost model whose
inputs are opinions produces conclusions that are opinions.

**X2 a prior is allowed, and must lose.** Before a rung has been observed there is no
median, and refusing to say anything is useless. So an ordering may stand in — clearly
marked as a prior, replaced by the first real observation, and never reported as though it
were measured.

**X3 a person is never summed with a model.** Two counters, always both, in every summary.
A release may not report one without the other.

**X4 an unrecorded rung is charged at the worst observed cost, not at a default name.**
Assuming a new mechanism is cheap is how a number stops meaning anything; assuming it is
"a model" is a guess in the other direction. The worst thing actually seen is the only
defensible answer and it is derived rather than chosen.

**X5 money is absent and says it is absent.** It needs a price table, `model/catalogue.py`
is a stub and `gates/model-vendor.md` is unrun. A currency this system cannot measure is not
reported in a unit that looks like it can.

**X6 cheaper compares like with like.** Two runs of the same workflow over the same steps.
Comparing across workflows measures the workflows.

## Decision rule, fixed now

- Categories survive only as a prior and as words for a person to read. Every number that
  decides anything — amortisation, retirement, whether this is getting cheaper — comes from
  observed seconds.
- If a rung has never been observed, that is reported, not filled in.

## What is deliberately NOT claimed

That seconds are what a run costs a business. They are what it costs the machine, which is
the thing this system can measure and change. Money arrives with the MODEL driver or not
at all.

## Result — 2026-08-30, by execution

    X2 an unobserved rung is marked a prior       chosen  2000.0 ms  (PRIOR, unobserved)
    X2 one observation beats the prior            chosen   440.0 ms  (3 seen)
    X2 and it is the median, not the last         of [0.40, 0.44, 0.60] -> 0.44
    X3 a person is never summed with a model      person=1 model=1 machine=2
    X4 an unknown rung is charged at the worst    some-new-mechanism 60000.0 ms
    X4 and is not counted as machine work         machine=0 model=1
    X6 a cheaper run is seen to be cheaper        900 ms -> 22 ms
    X6 no direction from two priors               both runs 1/1 estimated

    ASSERTED 0   LUMPED 0

**The case that decided the shape.** One person traded for three model calls reads as
60,000 ms -> 1,320 ms. Under the previous model both were `reasoned` and the trade was
invisible; under a single summed number it would have read as three times worse. It is the
largest improvement this system can make and it now has a number.

**X4 is derived, not chosen.** An unnamed rung is charged at the worst cost actually
observed, falling back to the worst prior when nothing has been. Charging it as "a model"
would have been a guess in the friendlier direction, which is the direction that flatters.

**Priors are visible in the summary**, as `3 estimated` beside the counts, so a number
resting on guesses cannot be quoted as a measurement by someone reading only the total.

## X1 closed, and the first measurement corrected the design

`run/harness.py` now times every step, records it on `StepRun.seconds`, and feeds
`Prices.observe`. A completed run rests on no prior at all -- a step that was seen is not an
estimate of itself.

**The first real run said the design was wrong.** Timing the whole step put `accessible` at
3267 ms. That is not what resolving costs; it is `browser/hand.py` pacing the press on
purpose, and it is the same seconds whichever rung answered. Pricing a rung that way
measures the pacing and drowns the difference the price exists to show.

Corrected to time the RESOLUTION alone, and the numbers separate cleanly:

    run 1   2 steps in 4399 ms    rungs {none: 1227, accessible: 3172}
    run 2   2 steps in 3845 ms    rungs {none: 1755, accessible: 2090}
            accessible  13.1 ms  (2 seen)

**Resolving costs 13 ms; the step costs three seconds and most of it is deliberate.** Both
are recorded: `StepRun.seconds` is what the run actually took, `Prices` is what a rung
costs. Neither is inferred from the other.

**The priors were wrong by two orders of magnitude**, which is what X2 exists for: MACHINE
was guessed at 10 ms against a measured 13 ms -- close by luck -- while the whole-step
figure it replaced was 3267 ms. A prior nobody replaces is a number nobody checks.

**A verb that resolves nothing is not priced.** `GO`, `SCROLL` and `KEY` return a resolution
time of zero and are skipped, rather than entering the table as a suspiciously cheap rung.
