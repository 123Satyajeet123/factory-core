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

## Result — 2026-08-30, by execution

    observed delta   disposition='derived'  RECORD_WRITTEN  match={'name': 'Ada Lovelace'}
    no change        disposition='none'     "snapshot captured but no new record"
    dom field map    disposition='none'     "no system-of-record observation captured"
    nothing at all   disposition='none'     "no system-of-record observation captured"

    mine: changed -> {'name': 'Ada Lovelace'} identifies=''
          keyed   -> {'name': 'Ada Lovelace', 'key': 'run-7f3a'} identifies='key'
          no-op   -> {}

**THE BLIND PREDICTION WAS WRONG, and in the better direction.** I expected `Effect` to be
replay-oriented -- a target and a value -- and to supply no evidence of change. It is
verification-oriented: `RECORD_WRITTEN`, `new_records`, `count_new_only`,
`forbid_collateral_loss`, `readback`, `idempotency_key`. Its own precedence is an observed
system-of-record delta first, a DOM field map next, an on-screen read-back next, a flagged
placeholder for a consequential act, and no effect last **with a reason** -- the same shape
as the witness ladder, arrived at independently.

**C6 satisfied: the contract is a view, not a second miner.** `Effect.match` is what a
contract binds. `factory/compile/mine.py` is about sixty lines and mines nothing itself.

**C1 holds.** The same snapshot before and after derives nothing, however consequential the
step looked. **C3 holds**: `disposition` is the vendor's own word for it and carries a
reason, so a refusal is visible rather than a quiet empty contract.

**A form field that took a value is not a record write.** The vendor flags it
`needs_operator_confirmation`; binding it would confirm the typing rather than the thing the
typing was for.

## The defect is narrowed, not closed, and the residue is now visible

Deriving from the delta stops a contract binding fields that were already true. It does
**not** by itself make CONFIRMED mean caused: the witness reads only the after-state, so a
record that already held the expected values still satisfies the contract.

What separates them is an **idempotency key** -- a value that exists only because we wrote
it. The vendor derives one when the destination issued it and the demonstration observed it,
and `Contract.identifies` now names that field. So:

    identifies == ""      CONFIRMED means PRESENT
    identifies == "key"   CONFIRMED means CAUSED

One word was quietly meaning both. It is now a field on the type, so promotion can weigh the
two differently and nothing has to infer which kind of confirmation it is holding.

**Still open:** nothing yet weighs them differently. `core/memory.Confidence` counts a
receipt without asking which kind, so a run full of presence-only confirmations promotes as
readily as one that proved causation. That is the next thing this makes possible and it is
not done.
