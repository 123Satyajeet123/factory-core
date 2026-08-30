# factory

Watches a browser workflow demonstrated once, then does it — and manufactures its own
tools while doing it.

Four claims, in the order they have to hold:

1. **It compiles.** A demonstration becomes a reviewable program that runs with no model.
2. **It proves.** Every effect is checked on a channel that did not cause it. Three-valued:
   confirmed, refuted, unverifiable — never a boolean that cannot be false.
3. **It manufactures.** Capabilities come from what actually happened, never from a
   model's idea of it. SkillsBench measured curated skills at +16.2pp and self-generated
   skills at ≈0; a model cannot reliably author the procedural knowledge it benefits from
   consuming. The procedure is read out of the record, and the only thing a model is asked
   for is a name.
4. **It keeps only what paid for itself.** Authoring is counted, not just execution.
   EvoClawBench measured skill workflows at 0.38 end-to-end token efficiency, and found
   empty scaffolds beating real skills — the gain was a context reset, not knowledge.
   A capability that never recovers its authoring cost is demoted.

And when it cannot proceed it asks, once, and the answer becomes part of the workflow.

## What self-evolving means here, and what it does not

The drivers do not rewrite themselves. The Darwin Gödel Machine does that — an agent
editing its own codebase, 20.0% to 50.0% on SWE-bench — and its own stated limits are the
reason this is scoped differently: it is bounded by a frozen model, its generalisation is
mostly in-domain, and it **assumes the benchmark is a faithful proxy for the ability**.
That assumption is the whole risk, and it is exactly where this system puts a witness
instead.

So: the capability library evolves, the drivers do not. What accumulates is procedures
read out of recorded evidence, verified on a channel that did not produce them, and kept
only while they pay for themselves. That is a narrower claim than self-modifying software
and it is the one that can actually be checked.

Cost is the second number, not the first. A workflow that needs a model every run is fine
if it works and can be shown to have worked; cheapness bought by checking less is not
improvement.

## Drivers

Each is one lifecycle, one vendor, one typed input and output, and one eval suite that
knows no workflow and no site.

| driver | converts | vendor |
|---|---|---|
| `browser/` | intent to acts, page to perception | playwright + raw CDP + ghost-cursor |
| `kernel/` | code to effects | prime-agent `rlm`, in its own venv |
| `model/` | context to a typed decision | anthropic |
| `witness/` | a contract and a destination to a verdict | none — ours |
| `memory/` | receipts to what is known, at what scope | ours for exact, a vendor for fuzzy |
| `capability/` | evidence to an installed, callable tool | the prime-agent skill format |

`compile/`, `run/`, `orchestrate/` and `authority/` are the line those sit on.
`core/` holds types and protocols and imports no driver.

## How things get built

Nothing here is hand-rolled that has a supplier. In order: use what the vendor exposes,
then the standard library, then write it — and only what has no supplier at all. A
reimplementation of a vendor capability is a defect, not a preference.

Where we deliberately do not use a vendor call, the file says which call and why —
`browser/guard.py` is the pattern.

Standard tooling throughout: pydantic for types, ruff, pytest, structlog, OTLP. No bespoke
framework, and no abstraction with one implementation.

`gates/model-vendor.md` is what that costs a vendor: litellm and instructor were declared
before they were measured, and both were dropped on measurement rather than defended.

## Using it

    uv run factory demonstrate "outreach"   # do the task yourself; it records what you did
    uv run factory demonstrate "outreach"   # again, on different inputs
    uv run factory compile "outreach"       # two demonstrations become a program

Two, because one demonstration cannot tell what varies from what is fixed. A demonstration
containing things that are not the task is ordinary — an aside becomes an optional step with
a guard, and a divergence the compiler cannot explain is refused as a question rather than
guessed.

## Loop

    ledger → compile → workflow → run → receipt → memory → compile

Evidence is the only upward flow, and everything that makes the system cheaper travels
on it.

## The ladder, which is where the cheapness comes from

Resolving which control a step means, in the order the answers cost:

    structural   free      what the demonstration recorded, still there
    chosen       a model   which of these is the one that was meant
    asked        a person  neither could tell
    remembered   free      either of the above, on every run after

Both expensive rungs end in the cheap one. A model's answer and a person's are kept the same
way — as a role and a name, which is what the free rung already searches by — so the run
after either costs nothing. That is the only reason asking is cheaper than a hardcoded
answer rather than more expensive.

A remembered resolution that no longer resolves descends again rather than failing, and
widens its scope only on witness receipts.

## What stops a run, and what it is not allowed to do

    a cap        code's, frozen, and nothing inside a run may raise it
    a goal       the work's: enough, declared once and checked per row by code
    a refutation something irreversible did not land — stops immediately
    grinding     rows that produce no receipt at all, one after another

An irreversible step does nothing without a permit, and a permit is consent with a budget
that gets spent. No permit means the act does not happen, and with nowhere to hold one there
is no permit: an unattended run cannot grant itself permission.

## Five rules

1. `core/` imports no driver; drivers import `core/` types.
2. Every driver is replaceable behind its `driver.py` — which is what makes six
   independent eval suites mean anything.
3. **No driver knows a destination.** `uv run python -m evals.agnostic` fails the tree if
   any file under `factory/` names a host, a selector or a product. Procedures over a
   destination are capabilities, and capabilities come from evidence through
   `capability/` — never from a file somebody wrote.
4. **No seam files.** Every vendor is used through documented API, and there is no
   subclass of a vendor type in the tree. An `extend/`-shaped folder appearing means we
   have gone deeper than tier 2 somewhere, and that needs a gate before it needs code.
5. **Order by truth is fixed; order by cost is learned.** `witness/ladder.py` is ordered
   by evidence quality and does not move. `run/select.py` is ordered by cost, which is an
   empirical claim about this step on this surface, so it is scored on outcomes.

## Running

    uv sync
    npm ci                         # ghost-cursor, and BotD for the detectability gate
    uv run factory vendors sync    # every pin, against what is actually on disk
    uv run ruff check .
    uv run pytest                  # read the exit code, never a piped tail

Read `gates/` first: one file per decision, criteria written before the code.
