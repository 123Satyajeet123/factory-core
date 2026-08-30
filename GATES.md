# GATES — M4 paid, and the preferences tier not built

## Not built, with the reason

`memory/preferences.py` was the obvious next thing and it is not built, because
`gates/memory-vendor.md` already settled it and because nothing in this tree produces or
consumes a preference. mem0 fails M3 (no `confirm`, no `refute`, no feedback surface of any
kind) and M5/M6 (will not construct without a credential). Building a tier with no producer
and no consumer would be a vendor adopted to fill a folder.

## M4 — the debt that gate recorded as owed, now paid

- [x] The defect is worse than the gate stated, and it is three lines to show:

      worked 50 times, then broke the last 3     bound=0.846  STAYS PROMOTED
      broke 3 times, then worked 50              bound=0.846  STAYS PROMOTED
      worked 8, broke 2, scattered               bound=0.490  demotes

  Counting receipts is order-blind. A resolution that worked all month and broke yesterday
  keeps its wide scope, and reads identically to one that was shaky early and has been fine
  since.
- [x] `Entry.until` — set by a witness refutation, cleared by a confirmation. `recall` walks
  past an entry whose validity has ended; `at()` still returns it, because elevate and
  demote read it and resolution does not.
  CHECK: uv run python -m factory.memory.driver
- [x] Both directions. A long record that broke is not answered with; proving itself again
  restores it; a narrower entry out of validity falls through to the wider one.
- [x] `demote` unchanged and still needed. Validity answers "is this true now"; the Wilson
  bound answers "was this ever reliable". Two questions, two mechanisms, neither doing the
  other's job.
- [x] Load-bearing. `Entry.standing` mutated to always return True -> `factory.memory.driver`
  goes red. 10 of 10 caught, 0 survived.
  CHECK: uv run python -m evals.mutation
- [x] Migration. An older store gets `ALTER TABLE entry ADD COLUMN until`, beside the same
  check already there for `caused`.

Zep's idea, not Zep. Not the streak counter I first reached for either — that needs a
threshold nobody derived.

## Deleted

`evals/affected.py` — mine, and a duplicate of `evals/which.py`, which discovers checks
instead of reading a hand-kept list and therefore cannot rot. Two mechanisms doing one job
is the defect; theirs is the better one.

## Verified, by name

    ruff                                clean
    evals.agnostic                      114 files, 0 that know a destination
    evals.mutation                      10 caught, 0 survived
    evals.which on the changed files    12 of 52 checks touched
    10 of those, non-browser            green
    evals.browser.cheaper_eval          FAULTS 0
    evals.browser.vertical_eval         FAULTS 0

## Failing, not mine

`evals.authority.permit_eval` — `run/select.target_for` now passes `wanted=` to
`browser.find` and the eval's `Counting` double does not accept it.
`TypeError: Counting.find() got an unexpected keyword argument 'wanted'`. In-flight work in
the other session; unrelated to validity.
