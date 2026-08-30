# When do the evals run?

**Not on their own, and not while somebody is editing.**

## Why

An eval here is not a unit test. It launches a real browser on a fixed debugging port, spawns
a second interpreter, binds loopback servers and drives a live page for tens of seconds. Half
a dozen of those firing under someone who is mid-edit takes the machine, takes the ports, and
reports failures about a tree that was being changed while it was read.

It also produces a worse signal than no signal: a suite that goes red because a file was
half-written teaches nobody anything, and after the third time it teaches people to ignore
red.

## The rule

- `uv run pytest` collects nothing. That is deliberate and this file is why.
  The mechanism is `conftest.py` at the root: `collect_ignore_glob = ["*"]`.
  `testpaths` and `--ignore` were not enough -- pytest still walked `candidates/`
  and collected 97 tests out of a vendored project, 15 of them erroring on import.
- An eval is run **by name**, when it is asked for: `uv run python -m evals.<name>`.
- Nobody runs the set as a matter of course. When the set should run, someone says so.

## What this is not

It is not a claim that the evals do not matter. They are how every gate in this directory
got its Result, and a gate whose Result cannot be reproduced by a command in the repo is
reopened. The rule is about *when*, not *whether*.

## What was removed

`evals/test_suites.py` — the collector that ran every suite as a pytest parametrisation. The
suites themselves are all still there and all still run by name. If the set is wanted back
under one command, that file is thirty lines and can return.
