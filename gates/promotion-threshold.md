# When has an entry earned a wider scope? SETTLED 2026-08-30.

**Rejected: a pair of constants.** "Three in a row" promotes noise, "twenty in a row"
never promotes, and both numbers would have been picked rather than derived.

**Settled: the lower bound of a Wilson interval on the entry's receipts.** One
threshold, carrying one meaning — how sure we insist on being. Sample size stops being
a separate knob: with a perfect record the bound is `n / (n + z²)`.

    3 / 3     0.44
    12 / 12   0.76
    30 / 30   0.89

Only witness receipts count. A refutation is evidence in the same arithmetic, so it
moves the bound down rather than merely blocking promotion.

**Measured rather than settled:** the threshold itself. `evals/memory` moves it against
recorded receipts and reports what each value promotes and demotes.
