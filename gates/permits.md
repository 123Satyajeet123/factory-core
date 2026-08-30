# What stops an irreversible act?

Written **before** reading any candidate or writing any code. `authority/permit.py` is empty
and the workflow this project is aimed at ends in sending mail to real people, so a replay
today would send. This is the only remaining gap on the list that is a safety gap rather
than a capability gap.

## The question, stated so it cannot be softened later

Not "is this principal allowed this action on this resource". That is authorisation, and it
is answered by a rule somebody wrote. The question here is:

> Has a PERSON consented to this specific irreversible effect, how many times, and is that
> consent still good?

A consent record with a budget, not a policy.

## Candidates, named up front so dropping one is visible

- **`openadapt_flow`'s own** — `Effect.needs_operator_confirmation` and `Effect.risk`
  already exist on the object our contracts are derived from, and its console has a
  governed decision surface. If risk is already assessed there, assessing it again here
  would be two mechanisms for one job.
- **oso**, **casbin**, **Open Policy Agent** — policy engines.
- **A model asked whether this looks dangerous** — named so that rejecting it is a decision.
  Expected to lose A1 outright: what is irreversible is a fact about the act, not a judgement
  to re-make per run.
- **Ours.**

## Criteria

**A1 what counts as irreversible is not decided in our source.** No list of verbs, no
"send", no host. It comes from what the demonstration and the compiler already established
about the effect. A rule naming an action is site knowledge wearing a safety hat, and
`evals/agnostic` should catch it.

**A2 a permit is CONSUMED, not merely held.** It carries a budget and the budget goes down
as it is used. A permit that authorises an unbounded number of sends is a rubber stamp, and
the difference between "you may email these nine people" and "you may email" is the whole
point.

**A3 absence refuses.** No permit means the act does not happen and a question is produced.
Not a warning, not a log line, not a default-allow with a flag to turn it off.

**A4 durable and scoped.** The answer outlives the run that asked, and a permit for one
workflow authorises nothing in another. Scope is the memory tiers that already exist.

**A5 revocable, and revocation takes effect on the next act.** A permit that cannot be
withdrawn is a decision a person made once and can never revisit.

**A6 the agent never holds the authority.** The permit is checked by the harness before the
act reaches the driver. It is never a tool a model can call, and never a field a model can
set. A model that can grant its own permission has none.

**A7 an unattended run cannot grant itself one.** If nobody is there to answer, the answer
is no. Measured by running with no answerer supplied and requiring the act not to happen.

## Blind prediction

The policy engines lose on **A2**. They evaluate a rule against a request and return
allow/deny; nothing in that shape is consumed, so a budget would be ours anyway and the
engine would only be answering the easy half. I expect the same for A5's immediacy.

`openadapt_flow` wins **A1** outright -- `Effect.risk` is assessed at compile time from the
demonstration, which is exactly where it belongs -- and I expect it to carry no consent
record at all, because its confirmation is a UI prompt rather than a durable grant.

If that holds, the split is: risk is theirs, consent is ours, and nothing is assessed twice.

## Decision rule, fixed now

- A1, A3 and A6 are pass/fail. Anything failing one is not adopted at any convenience.
- Take the risk assessment from wherever it already exists. Write only the consent record.
- If no candidate is adopted, say "searched, none fit" with what each lost on.

## Result — 2026-08-30, by execution

    no permit           acts=0  rows refused=3   asks: "send it -- button 'Send'"
    nowhere to hold one acts=0
    granted 2 of 3      acts=2  refused=1  left=0
    revoked after one   acts=1
    expired permit      good=False (with 9 unspent)
    another workflow's  acts=0
    FAULTS 0

Measured at a stand-in driver that counts what it was asked to do, so "the act did not
happen" is observed rather than inferred from a verdict.

**A1 is the vendor's, and it was already there.** `Effect.risk` defaults to `'reversible'`
and `needs_operator_confirmation` is a field, both assessed at compile time from the
demonstration. `compile/mine.irreversible` reads them. Nothing in our source names an
action, so `evals/agnostic` still passes -- a list of dangerous verbs would have been site
knowledge wearing a safety hat.

**A2 decided it, exactly as predicted.** casbin's whole `Enforcer` surface has nothing that
depletes a grant -- no budget, quota, consume, remaining, limit or expire -- and `oso` ships
no wheel for this interpreter at all. A policy engine answers allow/deny against a rule
somebody wrote; it holds no consent that is used up. So the budget would have been ours
anyway and the engine would have answered the easy half.

**A3, A6 and A7 hold.** No permit means no act, checked in `run/harness.py` before the
driver is called -- not a tool a model may call, not a field it may set. With nowhere to
hold a permit, nothing happens: an unattended run cannot grant itself permission.

**The split is what the prediction said: risk is theirs, consent is ours, nothing is
assessed twice.**

## What this does not do

Nothing yet ASKS. `authority/question.py` grew an `Authority` with an `Asks` seam while this
was being written, and the harness now takes both -- `memory` holds a permit, `authority`
asks for one -- but the asking is not wired to the refusal. Today a run refuses and records
the question; it does not offer it to anybody.

The budget is per step, not per row. Nine sends of one step spend one permit nine times,
which is the useful unit; a permit that had to be granted per row would be granted by
reflex, which is not consent.
