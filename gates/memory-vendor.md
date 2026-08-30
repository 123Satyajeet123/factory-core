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


# RE-OPENED 2026-08-30, because this gate was never executed

Everything above was settled by READING `rlm.harness` and reasoning about retrieval
semantics. No candidate was run. Of sixteen gates in this folder, nine were closed by
execution and this is one of the seven that were not -- and `gates/pointer-motion.md` is the
standing proof that reasoning is not enough: the blind prediction there was wrong, and only
running the thing showed it.

**The specific unmeasured assertion:** *"approximate retrieval over exact facts returns a
confident wrong answer."* That is the whole basis for owning `memory/facts.py`, and nobody
has ever seen it happen. It may be true. It is not evidence.

**And one candidate was noted in research and then dropped.** Zep/Graphiti carries
bi-temporal validity windows -- a fact with an interval that ENDS -- which is exactly what
`memory/demote.py` does crudely by moving an entry a tier. That was written down at survey
time and never followed up, which is the failure mode this project's own rules call out by
name.

## Candidates, all of them, named now

- **ours** (`memory/`) -- the incumbent. Exact keys, a three-tier scope chain, Wilson
  promotion on witness receipts, demotion by dropping a tier.
- **mem0** -- scopes `user`/`agent`/`run`/`app` with a ranked merge, which is this chain
  shipped. Extraction is LLM-driven.
- **Zep / Graphiti** -- bi-temporal validity. Facts that stop being true, with an interval.
- **Letta** -- OS-inspired tiers, agent-managed. Named so dropping it is visible.
- **`rlm.harness`** -- already spawned here for the kernel. Binary scope, no chain.

## Criteria

**M1 exact keys resolve exactly.** Two entries with similar keys at different scopes; asking
for one must never return the other. This is the assertion that was made without evidence,
and it decides whether `facts.py` is ours.

**M2 the scope chain resolves narrowest-first**, with nothing copied between tiers.

**M3 promotion is driven by EXTERNAL evidence.** A witness receipt moves an entry, not the
store's own opinion of salience. A store that decides what matters by extraction cannot be
told that a verdict refuted something.

**M4 invalidation.** A fact that stops being true must stop answering. Ours drops a tier;
bi-temporal ends an interval. Which is right is measured, not assumed.

**M5 what a lookup costs.** Ours is a SQLite row. A candidate needing an embedding, a
network round trip or an LLM call on the read path is priced, because resolution happens on
every step of every row.

**M6 what it drags in.** An LLM client, a vector store or a running service inside a driver
that must work with no key at all is a cost, not a detail.

## Blind prediction

M1 fails for the semantic candidates and M3 fails for all of them: none is built to be told
"a witness refuted this", because they infer importance rather than being told it. Ours
survives on M1 and M3 and loses M4 to Zep, whose interval is a better answer than dropping a
tier. If that holds, the outcome is a patch to `demote.py`, not a replacement of `memory/`.

If M1 passes for mem0, `facts.py` should not exist and I have been defending a file with a
story.

## Result — 2026-08-30, by execution

    mem0ai        2.0.19    8 deps   openai, qdrant-client, posthog, sqlalchemy
    graphiti-core 0.29.3    7 deps   neo4j, openai, posthog
    zep-cloud     3.28.0    5 deps   a client for a hosted service
    letta         0.16.8   69 deps   anthropic, datadog, clickhouse-connect
    ours                    0 deps   a SQLite row

    >>> Memory()                      # mem0, no credential
    openai.OpenAIError: Missing credentials ... set the OPENAI_API_KEY

    >>> Memory().add('button Save', user_id='op', infer=False)
    openai.OpenAIError: Missing credentials       # infer=False does not help:
                                                  # the constructor builds the embedder

    Memory API: add chat close delete delete_all entity_store from_config get
                get_all history project reset search update
    taking external evidence: NONE

**M3 fails for mem0, measured from its API rather than assumed.** There is no `confirm`,
no `refute`, no feedback surface of any kind. Its notion of what matters is inferred, and a
witness receipt is the one thing this system has that it cannot be told. Encoding receipts
in metadata and doing the Wilson arithmetic ourselves would mean the store is not doing the
job we adopted it for.

**M5 and M6 fail for every candidate on the facts tier.** Resolution happens on every step
of every row. mem0 cannot be CONSTRUCTED without a credential; graphiti wants a running
Neo4j; zep-cloud is a network hop per read; letta is 69 dependencies. `memory/facts.py`
must work with no key at all, and none of them can.

**M1 IS STILL UNMEASURED, and that is the honest headline.** The assertion that re-opened
this gate -- *approximate retrieval over exact facts returns a confident wrong answer* --
could not be tested, because mem0 will not start without a credential. So the decision below
does **not** rest on it, and the claim stays unproven. If it is ever tested and turns out
false, `facts.py` is still right for M3 and M5, but for two reasons instead of three.

**Decision: keep `memory/`, and the reason has changed.** Not because semantic retrieval is
wrong for exact keys -- nobody has shown that. Because a store that cannot be told a witness
refuted something cannot serve promotion, and a store that needs a credential cannot serve a
read path that runs on every step.

**M4 goes to Zep, unmeasured, and it is a real debt.** Bi-temporal validity -- a fact with an
interval that ENDS -- is a better answer than `demote.py` moving an entry a tier, because
"this stopped being true on the 30th" and "this was always shaky" are different facts that
our arithmetic currently renders identically. The idea is taken; the vendor is not, since it
arrives with Neo4j. Recorded as owed rather than dismissed: `core/memory.Entry` would need a
validity interval, and that is a change to `core/`.

## M4 — paid, 2026-08-30. The idea, not the vendor.

The debt above was recorded as owed. What it named turned out to be worse than stated, and
it is measurable in three lines:

    worked 50 times, then broke the last 3     bound=0.846  STAYS PROMOTED
    broke 3 times, then worked 50              bound=0.846  STAYS PROMOTED
    worked 8, broke 2, scattered               bound=0.490  demotes

Counting receipts is order-blind. A resolution that worked all month and broke yesterday
scores 0.846 and keeps its wide scope, and the arithmetic renders it identically to one
that was shaky early and has been fine since. Those are different facts and the store said
the same thing about both.

**Taken: a validity that ends.** `Entry.until` is set by a witness refutation and cleared by
a confirmation, and `recall` walks past an entry whose validity has ended. Not the streak
counter I first reached for, which needs a threshold nobody derived, and not a bi-temporal
graph, which needs Neo4j.

**What it costs is one descent.** An entry taken out of service is re-resolved on the next
run and restored the moment it works again, which is what `run/select.py` already does when
a remembered target no longer resolves. One mechanism, now at the right layer.

**`demote` is unchanged and still needed.** Validity answers "is this true now"; the Wilson
bound answers "was this ever reliable". The scattered case above demotes on the bound and
never ends its validity; the broken case ends its validity while its bound stays high.
Two questions, two mechanisms, neither doing the other's job.

**Load-bearing.** `evals/mutation.py` breaks `Entry.standing` to always return True and
`factory.memory.driver` goes red: 10 of 10 caught, 0 survived.

**Still owed:** the interval has one end. "This was true from the 3rd to the 30th" is a
question this cannot answer, and nothing asks it yet.