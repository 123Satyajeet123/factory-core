# GATES — the factory demonstrated, one machine at a time

15/15 checked. Run it with `uv run python -m demo.walk --reset --all`.
No eval and no test runs anywhere on this path; see `gates/when-evals-run.md`.

## The board is measured, not written
- [x] B1 Every module under `factory/` is classified by reading the import graph.
  CHECK: uv run python -m demo.walk 0
  EVIDENCE: "100 modules: 70 reachable and real, 6 orphaned, 24 with nothing in them".
  The count moves while the tree is edited, which is the point of measuring it.
- [x] B2 The board names the orphans, and it named the one that mattered:
  `factory.model.driver` was reachable from no command, so the `chosen` rung had no call
  site and the four-rung ladder was three rungs with a gap where the model goes.
- [x] B3 EMPTY, ORPHAN and UNSEEN are reported as three different states. 24 files were a
  docstring and no code, including `compile/refuse`, `browser/stealth`, `browser/tabs` and
  `run/retry` -- all named in README or PRINCIPLES as load-bearing.

## The surface is real and reproducible
- [x] S1 CHECK: uv run python -m demo.surface --check
  EVIDENCE: "4 people on :8801, a tracker on :8802; 2 controls share a name in the table
  and 1 is alone on /person; a write is answered with an id and read back on another
  endpoint".
- [x] S2 Ambiguity is derived, not asserted: station 1 reports "acts the table
  demonstration recorded as ambiguous: 2" from `Act.ambiguous`, and station 5 prints
  `AMBIGUOUS ON ITS OWN PAGE` against the step it produced.
- [x] S3 The write is a POST and the confirmation is a GET the page makes for itself.
- [x] S4 Nothing under `factory/` learns the surface. `demo/` is outside the tree
  `evals/agnostic.py` scans.

## The walk drives real machines
- [x] W1 CHECK: uv run python -m demo.walk --list -> 15 stations, runnable by number,
  `--from N`, `--all`, `--step`.
- [x] W2 Every station calls the product module. The only thing a station owns is the
  comparison.
- [x] W3 A demonstration is recorded through `browser/record.py` and lands in the ledger:
  "'outreach' #0: 11 acts", both origins, with exchanges and `among` per act.
- [x] W4 The program is induced with no model, and the compiler reports what will not run
  BEFORE anything runs.
- [x] W5 The witness answers. On this run the answer is UNVERIFIABLE, and the station says
  why rather than rounding it.
- [x] W6 The second number is reported: 10 steps, 29.8s, by rung {'accessible': 10}.

## Factory-driven and hand-driven are compared
- [x] H1 Every station carries HAND and a VERDICT. Final: 8 agree, 7 disagree, 0 undecided.
- [x] H2 Every disagreement is classified. Seven fixed in the product, five stated as
  limits, one (station 0) was my own misreading and says so.

## Ready to record
- [x] R1 CHECK: uv run python -m demo.walk --reset --all
  EVIDENCE: runs from an empty `~/.factory-demo` to a scored board in one command.
- [x] R2 A station that cannot run says why and the walk continues. Station 9 printed
  "not run: nothing has run yet. Station 8 first." when station 8 had raised.

## What the walk found, and what was done about it

Fixed in the product, each with the check that now fails if it regresses:

1. `browser/record.py` -- `Runtime.addBinding` does not survive a navigation unless
   `Runtime` is enabled. After one `goto` the page-side script still ran while the binding
   was `undefined`, and `say()` swallows that. **Every act after the first navigation was
   dropped in silence and the ledger looked complete.** One line: `Runtime.enable` first.
2. `browser/bodies.py` -- bodies were fetched at `responseReceived`, before the bytes
   arrive, so `getResponseBody` answered "No data found" and the body was dropped for good.
   Now gated on `loadingFinished`, held until the bytes land.
   CHECK: uv run python -m factory.browser.bodies
3. `browser/record.py` -- `close()` drained the instant recording stopped, so `Segment.after`
   missed the last act's effect, which is the only reason `after` exists. Now settles.
4. `browser/record.py` -- a `keydown` that is not text did not flush a pending write, so
   pressing Enter to submit recorded the Enter BEFORE the text it submitted. The induced
   program would press Enter on an empty field and then type.
5. `compile/mine.py` -- `events()` built one cumulative record stream across every surface,
   so an act's "effect" included another destination's traffic. Measured: the reveal step
   on :8801 was given a contract derived from the tracker's rows on :8802. **That is a
   false confirmation**, the exact failure this system exists to prevent. Now per-surface.
   CHECK: uv run python -m factory.compile.mine
6. `compile/induce.py` -- `workflow_of` skipped every state with no step. The vendor emits
   a LOOP whose body it does not put in the graph, so **eleven acts compiled to five that
   ran clean and did half the task.** Now a state the adapter cannot represent is a
   refusal, which is what `Induced.questions` is for.
7. `conftest.py` -- `uv run pytest` still collected 97 tests out of `candidates/` and
   errored on 15, so the rule in `gates/when-evals-run.md` did not hold. Now it does.

Found, not fixed, because each is a design decision rather than a defect:

- **A click that navigates loses its target.** `resolve()` runs off the handler and the
  page has changed by the time it asks what was at that point, so opening a person recorded
  `press main`. Replay then presses the page body, never navigates, and the run stops.
  Tried resolving concurrently with the drain; the navigation still wins, so it was
  reverted rather than left as a change that does not fix the mechanism. The real fix is
  that a click which navigates is a NAVIGATION -- which also gives `Doing.GO` the producer
  it has never had.
- **`Doing.GO` has no producer.** The recorder emits write/press/key/scroll/select and
  listens for no navigation, so no browser demonstration can produce a GO step.
- **Nothing arrives at the surfaces a workflow needs.** Every step carries its origin and
  no command opens one. The walk opens the tabs itself and says so.
- **`record_sets` ignores a lone object**, so `{"row": {...}}` -- what most APIs answer a
  write with -- carries no record, for the miner and the reader alike.
- **The miner sees insertions, not updates.** A status flipping on a record already there
  is not an effect it can see, and most real workflows change a record rather than make one.
- **A parameter is named after the TASK.** An `Act` carries no per-step intent, so every
  step hands the vendor the same one. A rows file for this workflow needs a column called
  `outreach`.
- **Corroboration is advice, not a gate.** `compile` and `run` never ask
  `capability/notice`, so the two-sitting threshold is printed by one command and obeyed by
  none.
- **Promotion did not fire.** Six confirmations left a WORKFLOW entry where it was; six
  refutations demoted it to EXECUTION. The ladder moves down and not up, which is the
  direction that makes runs more expensive rather than cheaper.
