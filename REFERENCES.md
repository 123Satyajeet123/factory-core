# What has already been measured

Two prior trees exist at `~/Projects/stealth/auto-workbench-mvp` and
`~/Projects/stealth/factory`.

**Nothing is copied from either.** They were written against different assumptions — a
Playwright actuator, two live kernels, a fixed cost-ordered ladder — and lifting code
would import those assumptions with it. What survives is what they *measured*, because a
number costs the same to reuse and does not carry a design in with it.

Read this list before deciding something it already answers. Do not read their source to
write ours.

## Measured, and not to be rediscovered

| finding | number |
|---|---|
| Reproducing stdout is an inverted filter for capabilities — a command that reads a file reproduces perfectly, one that does real work cannot | 15,115 shell calls, 16 of 103 admitted, every survivor a file read |
| A gate can pass with the gate deleted | the first PROVE gate: 9 of 9 tests green with the whole gate removed |
| Confidence is not evidence. A condition true on the motivating case can be true everywhere | a learned branch keyed on `"Clinical demo - all data is fake"`, a permanent subtitle, so it fired always |
| Injecting stealth patches costs signals rather than saving them | 4 signals against a clean control; a patched `navigator.webdriver` is an own property, a replaced function stringifies to its own source |
| Repetition alone is not a habit | twenty runs inside one afternoon is one experiment; corroboration must be across sessions |
| A capability must be checked for *discrimination*, not only reproduction | a procedure ignoring its arguments passes "did it reproduce" perfectly |
| Curated skills help; self-generated ones do not | SkillsBench, 7,308 trajectories: +16.2pp vs ≈0 |
| Skill workflows can cost more than they save | EvoClawBench: 0.38 and 0.30 end-to-end token efficiency; empty scaffolds beat real skills |
| Guards come from failures, not successes | ReUseIt: 24.2% → 70.1% mining both |
| A refutation after a send does not unsend it | the check must refuse before the act, not after |
| Building six machines before running one leaves them unproven | 25k lines, `run = 1`, never ended |

## Their open questions, still open

`~/Projects/stealth/factory` `probe/` is a four-vendor bake-off (browser-use, playwright,
pydoll, zendriver) that had produced no saved results as of 2026-08-30. Its `CONTACT.md`
predicts the finding that matters: nothing attempts a novel task for the first time.

If either produces a result, the number lands in this file. The code stays there.
