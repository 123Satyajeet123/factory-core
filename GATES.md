# GATES — architecture audit (expected vs built)

- [ ] G1 Every .py under factory/ and evals/ accounted for (read or classified as placeholder)
  CHECK: find factory evals -name '*.py' -not -path '*/__pycache__/*' | wc -l
  EXPECT: 147
  EVIDENCE: pending
- [ ] G2 Every folder in the pasted spec mapped to built/absent/renamed
  EVIDENCE: pending
- [ ] G3 Every vendors.toml row verified against what is on disk and against imports
  CHECK: uv run factory vendors sync
  EVIDENCE: pending
- [ ] G4 PRINCIPLES.md enforcement table checked line by line against code
  EVIDENCE: pending
- [ ] G5 Every gates/*.md read; Result present and re-runnable claim checked
  CHECK: ls gates/*.md | wc -l
  EXPECT: 18
  EVIDENCE: pending
- [ ] G6 Test suite + agnostic gate + ruff actually run, exit codes recorded
  CHECK: uv run pytest -q; uv run ruff check .; uv run python -m evals.agnostic
  EVIDENCE: pending
- [ ] G7 Analogy audit: factory/driver/sidecar/machine naming consistency across tree
  EVIDENCE: pending
- [ ] G8 Consolidation + formatting verdict with named files
  EVIDENCE: pending
