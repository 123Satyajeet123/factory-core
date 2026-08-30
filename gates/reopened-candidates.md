# Stagehand and Skyvern, reopened 2026-08-30. NOT YET DECIDED.

Both were excluded on grounds that no longer hold: Stagehand for being TypeScript,
Skyvern for AGPL over a network. Language and licensing are no longer constraints on
this project, so both exclusions were procedural rather than technical and neither
candidate was ever measured on the criteria below.

Criteria fixed here **before** either is read again. Same six that decided browser-use,
plus one the multi-language answer makes newly relevant.

- **C1 targeting** — does dispatch measure and refuse, or resolve and click?
- **C2 actor is not witness** — does `act()` return a verdict from a channel that did
  not perform the act? Re-reading the DOM after clicking is the same channel.
- **C3 tab choice** — a model decision, or an index or a title regex?
- **C4 response bodies** — can it hand over the JSON a page fetched for itself?
- **C5 whose browser** — the person's, over CDP?
- **C6 process boundary** — replaces C6-sync. A component in another language is a
  process we speak to, so the question is what the wire costs per act, not whether the
  domain must go async.

**Skyvern specifically:** AGPL obligations attach to distribution and to network use.
The decision to accept them is the operator's and is recorded as accepted; what still
needs establishing is which parts would be linked and what that obliges.

**Decision rule, fixed now.** Adopt per criterion, never wholesale. A candidate winning
C1 and C4 is worth an extend even if it loses the rest. If overlap turns out thinner
than claimed, shrink the claim rather than defend the evaluation.

## Result

(filled in after execution)
