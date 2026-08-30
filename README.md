# factory

Watches a browser workflow demonstrated once, then does it — cheaply, and with proof
that it happened. Not a recorded macro, and not a model re-reasoning every step.

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
