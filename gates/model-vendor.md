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



---

## Result — 2026-08-30, second pass. Everything that costs nothing is now measured.

`anthropic 1.2.0` is installed and declared. No credential still, so D1 and D3 stay open.
What follows was measured by execution against the installed packages, offline.

### instructor — DROPPED, and this did not need a call

    output_config    referenced in 0 files
    messages.parse   referenced in 0 files

Its Anthropic path is tool mode plus a reask loop (`v2/providers/anthropic/handlers.py:447`
echoes the assistant turn and returns a `tool_result` with `is_error`). That is a valid
conversation and it will not 400 -- the prefill worry in the gate above was wrong about
instructor specifically. What it is not is the native surface. Conformance comes from
retrying, which is D3 paid in tokens, for a constraint the provider now applies for free.
Principle 6: a reimplementation of a vendor capability is a defect, not a preference.

### D4 — nested union, three conversions, and the prediction was WRONG

Same shape: a discriminated union with a `Literal` discriminator, an enum and a bounded int.

    keyword         pydantic   openai/strict   anthropic transform   litellm filter
    const           kept       kept            -> description        kept
    enum            kept       kept            kept                  kept
    minimum/maximum kept       kept            -> description        kept
    discriminator   kept       kept            -> description        kept, DANGLING

**The provider SDK does not win D4.** `anthropic.lib._parse._transform.transform_schema`
degrades `const`, `minimum` and `maximum` into a description string -- `"{const: verb}"` --
so a discriminator stops being enforced and becomes advice. That is a deliberate choice
about what the constrained grammar can carry, and it is honest, but it is not what the
blind prediction said.

**litellm is worse, and it is a defect rather than a choice.** Its
`map_response_format_to_anthropic_output_format` calls `unpack_defs`, which inlines the
definitions and removes the top-level `$defs` -- and leaves `discriminator.mapping` still
pointing at `#/$defs/Ask` and `#/$defs/Verb`. Measured: `top-level $defs present: False`,
`refs still pointing at $defs: ['"#/$defs/Ask"', '"#/$defs/Verb"']`. The schema it puts on
the wire refers to definitions it deleted. This is what `conform.py` suspected, with a
cause it did not have.

### D5 — ours survives, and the seam is documented

Every strategy litellm ships scores on latency, cost, TPM/RPM, budget, tags, complexity or
shuffle: `lowest_latency`, `lowest_cost`, `lowest_tpm_rpm_v2`, `least_busy`,
`budget_limiter`, `tag_based_routing`, `simple_shuffle`, `complexity_router`,
`auto_router`. **None scores on whether the answer was usable downstream.** The claim in
`router.py` holds.

### D6 — real, and unearned

`CustomRoutingStrategyBase` is a documented extension point, so a second provider would
genuinely cost a config line. But there is one provider. The decision rule fixed above
says it: one interface over many providers earns its place when there are many providers,
and not before.

### litellm — DROPPED, and `router.py` goes with it

D5 is the only criterion litellm wins, and what it wins is the right to be subclassed.
Routing between our own model choices, when there is more than one, is a selection scored
on outcomes -- which `run/select.py` already is, for the locate ladder, using
`memory/confidence.py`'s bound. Two mechanisms for one job is the defect; there is no
second one to build.

### Adopted

    anthropic          the driver. Native output_config.format and strict tool use.
    ours               conform.py: what the transform degrades, stated per keyword,
                       so a schema is written knowing which constraints are enforced
                       and which are advice.
    ours               model choice, when there is more than one, through run/select.

### Still open, and not guessed

- **D1 conformance rate** and **D3 cost per admitted answer** need calls. Blocked on a
  credential; `ant auth status` reports profile "default" not configured.
- **Price.** `client.models.retrieve` carries `max_input_tokens`, `max_tokens` and
  `capabilities`, and no price field. Where a price comes from is its own gate.
- **D7 what a wrong answer costs downstream** needs the refusal path exercised against a
  real ambiguity, which is `evals/model` once D1 is unblocked.


## Result — D1, D2 and D7, by execution against models that cost nothing, 2026-08-30

    nvidia/nemotron-3.5-lightning:free    conformed 4/4  correct 4/4
        plain=0  near-miss=4  none=-1  the field=2
    minimax/minimax-m3:free               conformed 0/4  correct 0/4
        every ask: did not conform, 1 problem
    thinkingmachines/inkling-small:free   conformed 0/4  correct 0/4
        every ask: HTTP 403

**A free model does this job, and does it completely.** It told `button 'Save'` from
`button 'Save draft'` on "the control that saves without sending" -- the case designed to be
a near miss -- and answered **-1** when asked for a control that was not on the page.

**D7 holds, which is the one that mattered.** A confident wrong index presses the wrong
control and `browser/guard.py` cannot catch it: the guard checks that we hit what we aimed
at, never that we aimed at the right thing. Refusing had to be as easy to say as choosing,
and on this model it was.

**D1 is a rate, and the rate is the finding.** 4/4 against 0/4 between two models that both
cost nothing. A single number for "the model rung" would have been meaningless; per-provider
conformance is the measurement, and a provider failing it is not offered work needing it.

**D2 holds by construction.** Every failure above is a typed `Refused` carrying why -- a
malformed answer, a 403, an unreachable host -- and no exception escaped. A caller branches
without catching.

**D6 decided itself.** No client library is used. `response_format: json_schema` over a
plain POST reaches every OpenAI-compatible provider, a second one costs a base url, and this
gate's own decision rule says a dependency that only smooths an API we call once is not
adopted. `litellm` and `instructor` are not imported by this driver.

**"Free" came from the provider's own listing**, not from a table: 21 of 396 models at zero
prompt and completion cost. `litellm.model_cost` was never consulted, and the case it gets
wrong -- a published price on a model served free under an allowance -- is why.

## Still not measured

**D3 cost per admitted answer**, **D4 on a deeply nested schema** -- `Chosen` is an int and
a string, which is not `Found` -- and **D5 the router learning from a downstream verdict**,
which needs receipts from real runs.

**Groq's key returns 403** and was not tested. Two of three free models were unusable, which
is itself the argument for the router: the rung must fall through, and today the caller
passes a list.
