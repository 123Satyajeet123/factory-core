# Does the second run cost less than the first, for the same result?

Written **before** `run/select.py` exists. This is the product claim, and it has never been
measured in this tree or the last one.

## The claim, stated so it can fail

A step that needed a model once must not need one again. The expensive answer becomes a
cheap one, and the cheap one is used until something refutes it.

Not "the model gets better". Not "we cache". A RESOLUTION IS EVIDENCE: a model decided which
control was meant, a witness confirmed the act that followed, and the pair is worth more than
either. `memory/` already holds things at a scope and promotes them on receipts; this is the
first thing that has anything to put there.

## What already exists, so it is not rebuilt

`browser/locate.py` refuses on zero or two-plus and produces a Question. `Browser.find` takes
a `Chooses` and descends to it on a miss. `guard_eval` exercises that seam with a stub. What
is missing is the half that makes it compound: **nothing remembers what the chooser chose.**

## Criteria

**R1 the second run does not ask.** With the same step against the same page, run one
consults the chooser and run two does not. Counted at the chooser, not inferred from timing.

**R2 what is remembered is a TARGET, not an answer.** A stored node id is a fact about one
page load. What is kept is role and name -- the same thing `locate` searches for -- so the
cheap path on run two is the ordinary structural one and not a second mechanism.

**R3 a remembered resolution that no longer resolves falls back.** Pages change. If the
remembered target finds nothing, the run descends again rather than failing, and the stale
entry is not left to answer forever.

**R4 it is scoped and earned.** A resolution starts at EXECUTION scope. It widens only on
witness receipts, through `memory/promote.py`, like anything else. A model's own confidence
never moves it.

**R5 nothing is remembered from a refusal.** A chooser that declined, or a rung that was
blind, leaves no entry. Remembering a guess is how a wrong answer becomes permanent.

**R6 the saving is reported.** How many steps took the cheap path, and how many needed a
model. That number is the one this project is judged on, and it must be counted rather than
asserted.

## Blind prediction

R1 and R2 will hold. **R3 is where I expect this to be wrong**: I expect the first
implementation to remember a resolution and use it without checking that the page still
agrees, because the cheap path is the one nobody instruments. If the eval only tests the
happy case it will pass and be wrong.

## What is deliberately NOT claimed

That the model chose correctly. R1 measures that the second run is cheaper, not that either
run was right -- that is the witness's answer, and it is what R4 makes promotion wait for.

## Result — 2026-08-30, by execution

    run 1    rung=chosen       asked=1   chose button 'target'
    run 2    rung=remembered   asked=1   one match
    kept     {'role': 'button', 'name': 'target'} at execution
    moved on rung=chosen       asked=1   chose button 'renamed'
    declined rung=accessible   remembered=False
    FAULTS 0

**R1 holds and the count is where the cost is.** The chooser was consulted once across two
runs. Run two took the ordinary structural path -- `one match` -- because what was kept is a
role and a name, not an answer.

**R2 holds.** A node id is a fact about one page load; `{'role': 'button', 'name':
'target'}` is what `locate` searches by, so the cheap path is the existing mechanism rather
than a second one with its own failure modes.

**R3 holds, AND MY PREDICTION WAS WRONG IN A WAY WORTH RECORDING.** I predicted the first
implementation would use a remembered resolution without checking the page still agreed,
"because the cheap path is the one nobody instruments". It does check -- and it does because
writing that prediction is what made me write the fallback. The gate did its job by being
written first; claiming I got it right would be claiming credit for the gate's work.

**R5 holds.** A chooser that declines leaves nothing. The rung came back `accessible` -- the
structural refusal -- and memory is empty.

## The bottom rung, added 2026-08-30

    asked   rung=asked       person=1   a person said "button 'target'"
    after   rung=remembered  person=1   one match

Rung 0 refuses, the model declines, and a person is asked ONCE. What they said is kept
exactly as a model's answer would be -- a `Target` of role and name -- so the run after is
free.

**That is the only reason asking is cheaper than a hardcoded answer rather than more
expensive.** A question answered once and remembered costs a person a moment; the same
question asked every row costs them the job, and a selector written into our source costs
every other destination.

The ladder now has four rungs and both expensive ones end in the cheap one:

    structural   free      what the demonstration recorded, still there
    chosen       a model   which of these is the one that was meant
    asked        a person  neither could tell
    remembered   free      either of the above, on every run after

## Not done

**R6 is unbuilt.** Nothing counts how many steps took the cheap path against how many needed
a model, per run. That is the number this project says it is judged on, and it is still
asserted rather than reported. `witness/coverage.py` is the shape to copy: a tally that
names what to do next, not a percentage.

**R4 is half.** A resolution is stored at EXECUTION scope as the criterion asks, but nothing
yet feeds a witness receipt back to promote it, so it never widens. `memory/promote.py`
exists and has no caller — the same missing joint `capability/` has.

**No model has done any of this.** The chooser is a stand-in that counts. What is measured
is that the SECOND run is cheaper, which is independent of who answered the first.
