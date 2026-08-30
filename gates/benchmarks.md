# Do we run someone else's benchmark? SETTLED 2026-08-30, partly deferred.

Three 2026 benchmarks test this system's own claim. Their findings are load-bearing
here already:

- **EvoClawBench** — end-to-end token efficiency 0.38 and 0.30. Skill workflows cost
  more than direct execution once authoring was counted, and neither recovered without
  many reuses. Its ablation found empty scaffolds beating real skills, meaning the gain
  was a context reset. Adopted as `capability/amortize.py` and the empty-scaffold
  control in `evals/capability`.
- **SkillEvolBench** — separates learning from transfer with a frozen library and a
  raw-trajectory control, and scores resistance to shortcut solutions. Adopted as the
  metric vocabulary for `evals/capability`.
- **ReUseIt** — 24.2% to 70.1% by running variations in parallel and mining failures as
  well as successes. Adopted as `capability/variations.py` and `capability/failures.py`.

**Adopted now: their metrics.** They are the honest way to state our own claim.

**Deferred: running their task suites.** Their tasks are not browser work, and a
benchmark run before this system's loop has closed once measures the benchmark rather
than the system. Licenses unverified; check first.
