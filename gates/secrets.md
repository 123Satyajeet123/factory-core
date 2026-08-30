# A password demonstrated once is a password on disk forever

## What was measured, before any code

`browser/record.py` captures `String(el.value)` on every `input` event for any element with a
`value`. `<input type="password">` has one. `store/kept.py:37` then writes the segment with
`model_dump_json` into `~/.factory/ledger`, unencrypted.

So demonstrating a login writes the password to disk in plaintext, permanently — into the
one artefact this system says cannot be regenerated, which is also the one you cannot delete
and remake.

`browser/logins.py` says *"Import existing sessions once. We never see a password."* That is
the stance and it is a good one. It is not enforced anywhere, and a person demonstrating a
task that happens to include a sign-in defeats it without noticing.

## Criteria

**S1 never captured, not captured-then-redacted.** A value that reached a Python string can
reach a log, an exception, a repr, a model's context. The recorder must not send it in the
first place; redaction downstream is a second mechanism guarding the first one's mistake.

**S2 what is secret is what the PAGE says is secret.** `type="password"` and the
`autocomplete` tokens `current-password` / `new-password`. Not a guess from a field's name --
sniffing for "pass" catches `passenger` and misses `pw`, and both directions are bad.

**S3 the workflow still runs.** A reference is recorded in place of the value, so the
procedure is complete and replayable by anyone who has the secret. Recording nothing would
make the step un-inducible and the login un-automatable.

**S4 one reader, at the last moment.** Exactly one place resolves a reference to plaintext,
and it is the one that hands bytes to the page. Nothing else -- not a Did, not a StepRun, not
a ledger Act, not a prompt, not an exception.

**S5 the run's evidence carries the reference, never the value.** `Did.value` echoes what was
typed. For a secret it echoes the reference, or the leak moves from the ledger to the run.

**S6 provable by serialisation.** The check is: put a secret through record, compile, run and
witness, serialise everything to JSON, and grep for the plaintext. A property this important
is not asserted, it is searched for.

## Candidates for the store, named now

- **the environment**, read through `settings.py`, which already claims to be the only thing
  that reads it. No dependency, and it is where a key already lives.
- **`keyring`** — the OS keychain. The right answer for not holding plaintext at rest, and a
  dependency decision that belongs in its own gate rather than smuggled into this one.

Adopted now: the environment. `keyring` is named so choosing it later is a decision rather
than a discovery.

## What is deliberately NOT claimed

That this makes the system safe to hand a password to. It removes one specific leak that was
measured. The browser still holds the secret, the page still receives it, and a person who
can read the machine can read it.

## Result — 2026-08-30, by execution

    S1 a reference is not the secret            secret:example-com-password
    S4 exactly one call reveals plaintext       reveal, and nothing else
    S4 an unheld secret reveals nothing         None, not the reference
    S6 not in the ledger segment                reference only
    S6 not in the workflow                      reference only
    S6 not in the run evidence                  reference only
    S6 not in the contract                      reference only
    S6 not in a prompt fragment                 reference only
    S5 the evidence carries the reference       so the step is still replayable
    S3 someone holding the secret can run it    resolved at the last moment

    LEAKED 0   BROKE 0

**S6 is searched for, not asserted.** Every artefact is serialised and the plaintext is
grepped for. A property this important is not checked by reading the code that is supposed
to uphold it.

**The recorder never sees it.** `record.py` emits `secret:<host>-<field>` for an element the
page declares a password -- `type="password"` or the `current-password` / `new-password`
autocomplete tokens -- so nothing downstream has to remember to redact. Redaction would be a
second mechanism guarding the first one's mistake.

**`browser/driver.type` is the one reader**, and it resolves at the last moment: `Did.value`
echoes the REFERENCE while the page receives the plaintext. Without that the leak would
simply move from the ledger to the run.

**A missing secret refuses rather than types the reference.** `no secret held for
secret:x` with `NOT_PROBED`, which is a step that did not happen rather than a step that
signed in as the literal string `secret:x`.
