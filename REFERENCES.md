# Where to look before writing anything

Two prior trees exist. Both are working code, neither is this repo, and a session that
writes something already solved in one of them is repeating work that was paid for once.

## `~/Projects/stealth/auto-workbench-mvp` — ~25k lines, working

Take:

| from | what it knows |
|---|---|
| `witness/contract.py`, `channel.py` | three-valued verdicts, `blind_to`, counts not presence |
| `browser/hit.py`, `hand.py`, `stealth.py` | the hit-test rule, pacing, the audit that injects nothing |
| `factory/verify.py` | mutation testing over its own gates — the PROVE gate once passed all 9 tests with the gate deleted |
| `factory/worth.py` | 15,115 shell calls admitted 16 of 103, every survivor a file read: the filter was inverted |
| `factory/notice.py` | two thresholds — repetition *and* corroboration across sessions |
| `factory/prove.py` | the criterion is the witness, not stdout reproduction |
| `work/discriminate.py` | admitted on evidence it *separates*, never on confidence. A branch keyed on "Clinical demo - all data is fake" fired always |
| `work/render.py` | four layers; layer 3 refuses before the act, because a refutation after a send does not unsend it |
| `work/chain.py` | keep the whole model call — smolagents dropped 11 of 13 fields |
| `work/bundle.py` | secrets redacted at capture time, not at share time |

Do **not** take: its two kernels (smolagents and rlm, both live), `work/witness.py` (orphan,
zero importers), the ladder as a fixed sequence, or `determined_fraction` as a goal.

## `~/Projects/stealth/factory` — another session, ~4.6k lines, active

Blind machine specs written before any candidate was read: `BROWSER.md`, `KERNEL.md`,
`MODEL.md`, `WITNESS.md`, `FACTORY.md`. Take the discipline and the evidence — its
`FACTORY.md` cites SkillsBench at 7,308 trajectories, curated skills +16.2pp, self-generated
≈0, which is the sharpest statement of why a capability must come from a record.

`probe/` is a four-vendor browser bake-off (browser-use, playwright, pydoll, zendriver)
plus `kernel_jupyter.py` and two model stacks. It had produced no saved results as of
2026-08-30. Read it before re-deciding any browser vendor question.

`CONTACT.md` runs the factory against a real 16-minute recording with predictions written
first. Its P1 is the finding that matters here: nothing attempts a novel task for the
first time.

## Vendored sources

Anchors are named in the file that uses them — `browser/bodies.py`, `browser/guard.py`,
`kernel/session.py`, `compile/induce.py`. Read those before opening a vendor.
