# When does the factory ask a person, and how often?

A question is only cheaper than a hardcoded answer if it is asked once. Asked on every row of
every run it is more expensive than the lookup table it replaced, and more annoying.

## What was decided

**Identity is `(kind, about)`, never `because` or `candidates`.** Those are what the system
could see the LAST time it gave up; they change between askings. Keying on them asks a person
the same thing on every run. Re-asking refreshes what was seen and leaves the answer alone.

**Every kind must reach a destination.** `Ask.TARGET`'s answer names a control;
`Ask.PARAM`'s names the column that supplies a workflow parameter, and `run/harness.supplied`
reads the row through it. A kind whose answer goes nowhere is a defect, not a spare — which
is why `PARAM` was added only when the harness could act on it, and why the harness had been
filing missing parameters as `TARGET` until then.

**Nobody answering is a state, not an error.** `Asks` may return None — no person at the
keyboard, or they declined. The question stays open, `waiting()` lists it, the caller gets
None and refuses, which is what it would have done anyway. What must not happen is asking in
a loop inside one run.

**An answer outlives the run that needed it**, which is the whole point: per-destination
knowledge enters the system as data rather than as a line of per-destination code, and
`evals/agnostic` can go on insisting no driver knows a destination.

## Measured

    six asks of one settled question    the person was bothered once
    a fresh Authority on the same store still answered, without asking
    two workflows wanting `note`        asked separately: file-a-note.note, other-thing.note
    a second row of the same workflow   did not re-ask

Counting is the only way to check "asked once"; asserting it passes trivially.
