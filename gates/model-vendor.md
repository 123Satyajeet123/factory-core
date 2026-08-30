# What does a typed decision need, and who supplies it?

Written **before** a line of `model/`. The README already names a vendor — `litellm +
instructor` — and that line was written without a survey, which is the rule's own stated
failure mode. A declared vendor is a prediction, not a decision.

## Why this is opened now rather than later

`core/drivers.Chooses` exists, `browser/driver.find()` calls it, and `guard_eval` L1
passes with a hand-written stub that picks a known string. The socket is built and tested;
what is missing is the occupant. That is the same shape the WITNESS work had, and it is why
this driver is cheap to add and expensive to get wrong: rung 1 of the locate ladder costs a
model call on every ambiguity, forever.

## What is already established, so it is not re-litigated

- **The job is narrow.** `driver.py`: a situation and a schema in; that schema or a typed
  refusal out. Not a chat client, not an agent loop, not a framework.
- **A job is a schema, never a driver.** `model/schemas/` holds one per job — resolve,
  classify, reason, diagnose, grade, amend, name. Adding a job adds a schema and nothing
  else.
- **`name` is the only thing the factory asks a model for.** Everything else is asked
  during a run, by a rung that could not answer more cheaply.
- **Nested models are a known bad path.** `conform.py` says so. Whatever is adopted has to
  be measured on nesting, not on a flat example.
- **The ladder descends only on a miss.** `locate-ladder.md` L5. A model call is rung 1 and
  is not reached when role and name resolve.

## What the provider actually offers now, read 2026-08-30

This is the fact that decides the gate, so it is written down before the candidates rather
than discovered inside one:

- **Structured output is native.** `output_config: {format: {...}}` on `messages.create`,
  and `client.messages.parse()` validates the response against a schema. The older
  top-level `output_format` is deprecated.
- **Strict tool use is native.** `strict: true` on the tool definition — top level, beside
  `name` and `input_schema`, not on `tool_choice` — with `additionalProperties: false` and
  `required`, guarantees `tool_use.input` validates exactly.
- **Assistant prefill is gone** on every current model. Any library whose conformance trick
  is prefilling a `{` is broken here and will fail closed rather than loudly.
- **The Models API answers capability, not price.** `client.models.list()` and
  `.retrieve(id)` carry `max_input_tokens`, `max_tokens` and `capabilities`. There is no
  price field and no `context_window` field.

**That last point cuts against our own stub.** `catalogue.py` says "each provider own
/models" because "litellm model_cost is a 3,364-row table, and a table reports prices
nobody paid". The live endpoint does not carry prices, so it replaces the capability half
of that table and not the cost half. Where a price comes from is still open, and pretending
`/models` settles it would be the convenient answer rather than the measured one.

**instructor was built for a world where the first two bullets were false.** Its value is
retry-and-validate around models that could not be constrained. That world ended. Whether
it still earns a dependency is exactly what D1 and D2 measure.

## Candidates, named up front so dropping one is visible

- **The provider SDK alone** — `messages.parse()` / `output_config.format` / `strict: true`.
  One dependency, no abstraction, no second failure mode.
- **litellm** — one interface over many providers, plus routing. The routing is the part
  `router.py` wants; the interface is the part that may cost more than it saves.
- **instructor** — retry-based validation over a provider client.
- **outlines**, **guidance** — constrained decoding. Aimed at local weights; likely the
  wrong shape here, and recorded as considered rather than silently skipped.
- **Pydantic AI**, **BAML** — typed-call frameworks. A framework where a function is needed
  is principle 11's failure, but they are named so dropping them is visible.

## Criteria

**D1 conformance without a retry.** Ask for a schema; does the first response validate?
Measured per provider and reported as a rate, not as "it worked". A library whose
conformance comes from retrying is paying for correctness in tokens, and D3 will show it.

**D2 a refusal is typed, not thrown and not guessed.** When the model will not or cannot
answer in the schema, the driver returns a typed refusal that a caller can branch on. An
exception is not a refusal, and neither is a best-effort object with empty fields — that is
the shape that makes `locate` press the wrong control.

**D3 cost per admitted answer.** Not cost per call. An answer the compiler could not use
was paid for and produced nothing, so the denominator is admitted answers. Retries,
reprompts and discarded responses all land in the numerator.

**D4 nesting, because flat is not the case we have.** `Found`, `Target` and a candidate set
are nested. Measured on a nested schema; a candidate that passes flat and fails nested has
failed, and `conform.py` exists because that was already suspected.

**D5 the router learns from a downstream verdict.** `router.py`'s claim is that no vendor
strategy scores on whether the answer was *usable* — only on latency, cost or errors. Test
it: can a strategy be scored on whether the compiler accepted the output? If a vendor
already does this, ours is deleted.

**D6 a second provider costs a config line, not a code path.** The point of an abstraction
here is provider substitution. If adding one means editing the driver, the abstraction did
not do its job and the provider SDK alone was the cheaper answer.

**D7 what a wrong answer costs downstream.** A chooser returning a confident wrong index
presses the wrong control, and `browser/guard.py` cannot catch that — the guard checks that
we hit the element we aimed at, not that we aimed at the right one. So D2's refusal path is
load-bearing in a way a conformance rate does not capture, and the eval must include a case
where the right answer is "none of these".

## Blind prediction, recorded before measuring

The provider SDK alone wins D1, D2 and D4, and instructor is deleted. litellm survives on
D6 alone, and only if a second provider is actually wanted. `router.py` survives D5.
`catalogue.py` shrinks to capability lookup and the price question moves to its own gate.

Writing this down so that being wrong is visible, the way `pointer-motion.md` was wrong
about our own curve.

## Decision rule, fixed now

- Adopt per criterion. Routing and conformance are separate jobs and may have separate
  answers, or none.
- A dependency that only smooths an API we already call once is not adopted. "One interface
  over many providers" earns its place when there are many providers, and not before.
- If the provider SDK wins outright, the README line is corrected rather than defended.

## What is deliberately NOT claimed

That a conforming answer is a correct one. D1 measures shape. Whether the choice was right
is `evals/model`'s third question — does the score predict the verdict — and that cannot be
answered until the WITNESS is producing receipts on real runs.

## Result — 2026-08-30, PARTIAL. The half that costs nothing is measured; the rest is blocked.

**What is installed, and it is not what the gate assumed:**

    litellm     1.83.0     declared in pyproject
    instructor  1.16.0     declared in pyproject
    openai      2.16.0     pulled in, not declared
    anthropic   NOT INSTALLED

**The provider SDK whose native surface decides this gate is not in the tree.** D1 and D2
turn on `messages.parse()`, `output_config.format` and `strict: true` — the things that made
instructor's retry-and-validate loop unnecessary. None of that can be measured here, because
the package that carries it was never added. Meanwhile `instructor` and `litellm` are
declared and an `openai` client arrived as a transitive dependency of one of them.

That is the finding, and it is available for free: **the tree is provisioned for the
conclusion the gate was opened to test.** Adopting on a README and then installing to match
is how a survey stops being possible.

**Blocked on two things, both the operator's:**

- `anthropic` is not a declared dependency. Adding it is a decision, not a detail.
- No credential. `ANTHROPIC_API_KEY` is unset and `ant auth status` reports profile
  "default" not configured.

**What running it will cost.** D1 is a conformance *rate*, so it needs repeated calls per
candidate per schema — the flat case and the nested one `conform.py` already suspects. That
is real money on someone's account, and it is not spent without being asked.

**Not adopted, not rejected, and deliberately not guessed.** The blind prediction above
stands unmeasured. Nothing in `model/` should be written against it until this section
carries numbers, because a driver built to a prediction is the prediction made permanent.
