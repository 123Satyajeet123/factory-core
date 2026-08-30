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

The machines do not rewrite themselves. The Darwin Gödel Machine does that — an agent
editing its own codebase, 20.0% to 50.0% on SWE-bench — and its own stated limits are the
reason this is scoped differently: it is bounded by a frozen model, its generalisation is
mostly in-domain, and it **assumes the benchmark is a faithful proxy for the ability**.
That assumption is the whole risk, and it is exactly where this system puts a witness
instead.

So: the capability library evolves, the machines do not. What accumulates is procedures
read out of recorded evidence, verified on a channel that did not produce them, and kept
only while they pay for themselves. That is a narrower claim than self-modifying software
and it is the one that can actually be checked.

Cost is the second number, not the first. A workflow that needs a model every run is fine
if it works and can be shown to have worked; cheapness bought by checking less is not
improvement.

## Machines

Each is one lifecycle, one vendor, one typed input and output, and one eval suite that
knows no workflow and no site.

| machine | converts | vendor |
|---|---|---|
| `browser/` | intent to acts, page to perception | browser-use, plus three patches |
| `kernel/` | code to effects | prime-agent `rlm`, in its own venv |
| `model/` | context to a typed decision | litellm + instructor |
| `witness/` | a contract and a destination to a verdict | none — ours |
| `memory/` | receipts to what is known, at what scope | ours for exact, a vendor for fuzzy |
| `capability/` | evidence to an installed, callable tool | the prime-agent skill format |

`compile/`, `run/`, `orchestrate/` and `authority/` are the line those sit on.
`core/` holds types and protocols and imports no machine.

## Loop

    ledger → compile → workflow → run → receipt → memory → compile

Evidence is the only upward flow, and everything that makes the system cheaper travels
on it.

## Three rules

1. `core/` imports no machine; machines import `core/` types.
2. Every machine is replaceable behind its `machine.py` — which is what makes six
   independent eval suites mean anything.
3. **One seam file.** `browser/bodies.py` is the only code that attaches to a vendor
   object, and `model/router.py` the only strategy subclass. Everything else uses a
   vendor or conforms to its format. A second `extend/`-shaped folder appearing means
   we have gone to tier 3 somewhere, and that needs a gate before it needs code.
4. **Order by truth is fixed; order by cost is learned.** `witness/ladder.py` is ordered
   by evidence quality and does not move. `run/select.py` is ordered by cost, which is an
   empirical claim about this step on this surface, so it is scored on outcomes.

## Running

    uv sync
    uv run factory vendors sync
    uv run ruff check .
    uv run pytest                  # read the exit code, never a piped tail

Read `gates/` first: one file per decision, criteria written before the code.
