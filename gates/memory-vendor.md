# Who stores memory? SETTLED 2026-08-30, by reading the vendor.

`rlm.harness` has typed entries, versions, a refinement log, and an `overview()` that
renders state into a prompt. Its scope is binary — `local` or `global`.
`HarnessEntry.path` exists but `list()` filters only on kind and scope. So the vendor
offers storage and rendering, not scope resolution.

**Settled, and the split is by retrieval semantics rather than by tier:**

- `memory/facts.py` — ours. Aliases, targets, source locations, permits. Exact keys,
  resolved narrowest-first. Approximate retrieval here returns a confident wrong
  answer, which is worse than returning none.
- `memory/preferences.py` — a vendor's, where similarity is the right question. mem0's
  scopes (`user`, `agent`, `run`, `app`) already rank a merge the way this chain does.
  Deferred until the main tier holds anything worth retrieving fuzzily.
- Skills stay in `rlm.harness` — the kernel's registry of what is callable is a
  different question from what the system knows.

**Re-open when** the main tier has real content and exact lookup is measurably losing
answers a person would say were there.
