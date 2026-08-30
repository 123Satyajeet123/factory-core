# What makes a verdict trustworthy, and who supplies it?

Written **before** reading any candidate and before a line of `witness/`. This is a first
decision, not a re-decision, so the criteria below are fixed here and a convenient library
cannot move them afterwards.

## Why this is opened at all, given the README says "none — ours"

The README's machine table records the WITNESS vendor as `none — ours`. That was written
without a survey, which is the rule's own stated failure mode: *skipping the search because
a thing looks easy to write*. Judging is not one job. It is reading bytes into fields,
checking fields against a contract, and ranking evidence — and the first two have
maintained suppliers in every language. "Ours" may still be the answer for the third. It
has to be measured to be claimed.

## What is already established here, so it is not re-litigated

- **The thesis is measured, in this tree, by accident.** `machine.type()` returned
  `Did(ok=True)` while dispatching zero `keydown` events — `type="char"` then `type="keyUp"`,
  so a page saw `keypress`+`input`+`keyup` with `event.key` empty. The text still landed in
  the field. Every green check stayed green. What caught it was `record.py` reading the
  page's own event stream: a channel that did not perform the act. The witness machine is
  the thing that makes that repeatable instead of lucky.
- **A refutation after a send does not unsend it.** The guard refuses *before* the act; the
  witness judges *after* it. They are not two implementations of one idea and neither
  substitutes for the other. A verdict is for what may be promoted, never for what may be
  dispatched.
- **An easy check is an inverted filter.** Measured in a prior tree: reproducing stdout
  admitted 16 of 103 shell capabilities and every survivor was a file read. A criterion a
  no-op satisfies selects for acts that do nothing.
- **Two scores or the gate is meaningless.** `gates/browser-guard.md` established the shape:
  a guard that always refuses is trivially safe and useless, so SAFETY and LIVENESS are both
  reported every time and a release may not trade one for the other. The witness inherits
  this exactly.
- **One reader exists.** `witness/readers/fetched.py` reads what the page fetched for itself.
  `readers/__init__.py` says "discovered by entry point", so the socket is already a plugin
  point with a single occupant.
- **`perceive_eval` already names the hole.** DOM and WIRE are readable; PAINTED is readable
  by neither, and "what neither can see is the finding".

## Candidates, named up front so dropping one is visible

Split by the job, because adopting per criterion means adopting per job.

**Reading bytes into fields** — `jsonpath-ng`, `jmespath`, `glom`, `pandas.read_html` /
`read_csv`, stdlib `csv` + `json`.

**Checking fields against a contract** — `pydantic` (already a dependency), `jsonschema`,
`pandera`, `great-expectations`, `deepdiff` for state deltas.

**Ranking evidence / the ladder itself** — no candidate identified. If the survey finds
none, that is recorded as "searched, none found", never assumed.

**Mining the effect a step should have had** — `openadapt_flow.compiler.effect_mining`,
already a tier-1 vendor here, already produces effects from a state delta. Whether a
witness contract can be derived from the same object is a question for this gate, because
deriving it twice is two mechanisms doing one job.

## Criteria

**W1 the channel did not perform the act.** Given a `Did` produced by dispatch, the verdict
must come from bytes dispatch did not produce. Re-reading the DOM after clicking is the same
channel and fails this. Measured by construction and by fixture: a page that reports success
in the DOM while its own fetch says otherwise must not be confirmed.

**W2 false confirmed is the gate, and both scores are reported.**

    FALSE CONFIRMED   confirmed when the effect did not happen     must be 0
    BLIND             unverifiable when it plainly did happen      budgeted, not 0

A witness that never confirms passes the first and is useless. A release may not trade the
first for the second.

**W3 blind refuses rather than guesses.** A rung that cannot see a field the contract binds
returns `unverifiable`. It never falls back to a weaker signal silently, and it never
returns `confirmed` on a partial read.

**W4 unverifiable is counted, not swallowed.** The fraction of acts the system could not
witness is reported per run. It is the ceiling on promotion, which is the ceiling on
cheapness, which is the product claim — and it is currently invisible because `unverifiable`
moves neither side of the Wilson arithmetic.

**W5 a no-op cannot be confirmed.** A step that does nothing, against a contract that binds
real fields, must come back refuted or unverifiable — never confirmed. This is the inverted
filter, and it is the criterion most likely to be quietly failed.

**W6 the reader knows no site.** A reader binds on shape, never on a selector, a URL or a
field name a person chose. `fetched.py` is the standard: lists of objects with shared keys
in a structured body, CSV as a fallback, and it derives what it can see so blind refuses
rather than guesses.

**W7 order by truth does not move.** The ladder is ordered by evidence quality. A lower rung
never overrides a higher one, and the order is not scored on outcomes — that is `run/select`,
which is a different question with a different answer.

**W8 what a verdict costs.** Rung 0 must be free: bytes already collected for another reason.
The bottom rung is a model call and is priced. Reported per verdict, because "cheapness
bought by checking less is not improvement" cuts both ways — so does confidence bought by
paying for a model on every step.

## One design question this gate must settle, because it changes `core/contract.py`

**Is a verdict synchronous?** Today `run/step.py` reads "perform, expect on the same
channel, witness on one that did not perform" — all within the step. But some confirmations
arrive later: a webhook, an emailed receipt, a nightly export, a record visible only on the
next page load. If `Verdict` admits a pending state, `Receipt` needs a reconciliation pass
and `orchestrate/maintain.py` is where it runs. If it does not, then every
later-arriving confirmation is permanently `unverifiable` and W4's number is structurally
inflated.

Decide before the types are written. Changing it afterwards changes `core/`.

## Decision rule, fixed now

- Adopt per criterion and per job, never wholesale. A library that wins the reading job is
  worth a dependency even if it supplies no judging at all.
- If no candidate wins the ladder, keep ours and record "searched, none found" with what was
  searched — never adopt something to have adopted something, and never claim "ours" without
  the search.
- A reader is a plugin at an entry point or it is not a reader. Anything that must be edited
  into a ladder to add a surface has made perception un-extendable, which is the ceiling this
  machine exists to raise.

## What is deliberately NOT claimed

That `confirmed` means the work was correct. It means the effect the contract named was
observed on a channel that did not cause it. A workflow can be confirmed and wrong, and the
gap between those is `compile/`'s problem and a person's, not this machine's.

## Result

(filled in by execution — not by reasoning)
