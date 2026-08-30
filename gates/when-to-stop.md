# What makes a run stop?

Written **before** `run/stop.py` exists. Today `over()` walks every row it is given and
stops when they run out. That is the only condition, and it is the one that never protects
anybody.

## Two different things, and conflating them is the trap

**A cap is code's, outright.** How many rows, how long, how much. It is not a judgement, it
is not negotiable, and no model or workflow may raise it.

**A goal is the work's.** "Until the nine are contacted", "until the list is exhausted".
Written once, when the workflow is compiled or when a person says so, and CHECKED PER ROW BY
CODE. A model deciding per row whether to continue is both expensive and the shape this
project refuses everywhere else -- it would re-reason a settled question on every iteration.

## Candidates, named up front

- **Ours, a declaration** -- a small typed goal the harness evaluates.
- **Ours, a predicate the model writes as code** -- the rung-2 shape. Named so that
  rejecting it is a decision: it puts model-written code on the safety path, and a cap that
  a cell can rewrite is not a cap.
- **A workflow engine's** (Temporal, Prefect, Airflow) -- they have retries, timeouts and
  cancellation. Expected to lose on C3: their stopping is about failure, not about enough.

## Criteria

**C1 a cap cannot be raised from inside the run.** Not by a workflow, not by a model, not by
a step. Measured by trying.

**C2 stopping says which condition stopped it**, and the reasons are distinguishable:
finished the work, hit a cap, something irreversible was refuted, nobody could answer a
question, or it was grinding. A run that says only "stopped" is a run nobody can act on.

**C3 enough is not the same as failure.** A run that did what it was for stops CONTENT. A
run that hit a cap stops with work left. Both are ordinary; only one is a problem, and a
system that cannot tell them apart reports the wrong one.

**C4 a refuted irreversible act stops the run immediately.** Not at the end of the row, not
after a retry. If something that cannot be undone was done and the witness says it did not
land, continuing is reckless -- the next row would do it again.

**C5 grinding is a stop.** Rows that refuse for the same reason, one after another, are not
progress. What counts as grinding must be derived from the run rather than picked: the
honest condition is consecutive rows that produced NO receipt at all, because a run learning
nothing is a run that will keep learning nothing.

**C6 the cap is reported even when it was not reached.** How much was left is what tells a
person whether the cap is right, and a number only shown on failure is a number nobody
tunes.

## Blind prediction

C5 is where I expect to be wrong. The temptation is to pick a threshold -- three failures,
five -- and I expect the first implementation to do that and to look reasonable. The number
would be arbitrary and would fire on a workflow whose fourth row is legitimately hard.

## Result

(filled in by execution — not by reasoning)
