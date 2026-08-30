# Where does a contract come from, so that CONFIRMED means the act caused something?

Written **before** reading `openadapt_flow.compiler.effect_mining`.

## The defect this exists to fix

`witness/readers/fetched.py` answers "a record with these values is there". It cannot answer
"this act put it there". A record that already existed confirms, so CONFIRMED today is
weaker than it reads, and the gap is in the CONTRACT rather than in the reader: a contract
binding what merely exists can only ever be checked for existence.

A contract that binds what CHANGED cannot be satisfied by the previous state. That is the
whole fix, and it moves the problem to where the evidence is.

## Candidates, named up front so dropping one is visible

- **`openadapt_flow.compiler.effect_mining`** — tier 1 here already, and it turns a state
  delta into `Effect` objects. If a contract falls out of the same object, deriving one
  separately would be two mechanisms doing one job.
- **`deepdiff`** — a general structural delta between two states.
- **Ours, over `Did.exchanges` before and after** — the bodies are already collected.
- **A model, asked what should be true afterwards** — named so that rejecting it is a
  decision rather than an omission. Expected to lose C2 outright.

## Criteria

**C1 binds what changed, never what was already true.** Given a before and an after where a
field held the same value throughout, that field must not appear in the contract. Measured
by fixture: a contract derived from a no-op must bind nothing.

**C2 no model is on the path.** Derivation is mechanical. A model deciding what should be
true afterwards is the answerer marking its own paper, one step removed — and SkillsBench
measured self-generated procedural knowledge at ≈0.

**C3 refusing is a legitimate output, and a visible one.** When a delta supports no binding,
the contract is empty and `judge` already returns UNVERIFIABLE for it. That must show up in
`witness/coverage.py` as demand rather than as a quiet pass.

**C4 no site knowledge.** No field-name table, no host, no per-destination map.
`evals/agnostic` applies unchanged.

**C5 what it binds, something can read.** A derived contract whose fields no admissible
reader can address is blindness, and it must be reported as blindness rather than as a bad
contract. The two have different fixes: one needs a reader, the other needs a better delta.

**C6 one mechanism.** If the vendor's `Effect` carries what a contract needs, the contract
is a view of it. If it does not, the gap is named before anything is written.

## Blind prediction

**Their `Effect` is oriented to REPLAY, not to verification.** I expect it to describe what
to DO again -- a target and a value -- rather than what was OBSERVED to change, because that
is what a compiler needs. If so it supplies the value but not the evidence of change, and
what we want is the before/after state `mine_step_effects` consumes rather than what it
returns.

If that is wrong and `Effect` already carries an observed delta, this is a view over their
object and almost no code, which is the better outcome.

## Decision rule, fixed now

- C1 and C2 are pass/fail. A derivation failing either is not adopted at any convenience.
- Adopt the vendor's object if it carries the delta; adopt its INPUT if it does not; write
  a derivation only if neither is reachable, and say which.
- If the honest answer is that no contract can be derived for a shape of act, that shape is
  UNVERIFIABLE and `coverage` counts it. Inventing a bindable field to raise the number is
  the failure this gate exists to prevent.

## Result

(filled in by execution — not by reasoning)
