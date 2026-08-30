"""Is a cost measured or assigned, and does a person show up as a person?

    uv run python -m evals.observe_eval

No browser and no site. See gates/cost-model.md.

    ASSERTED  a prior was reported as though it had been measured   must be 0
    LUMPED    a person was summed into a number with a model        must be 0
"""

from __future__ import annotations

import sys

from factory.core.contract import Receipt, Verdict
from factory.core.evidence import Did, RowRun, Run, StepRun
from factory.observe import PRIOR, Prices, cheaper, spent


def a_run(*rungs: str, verdict: Verdict | None = None, timed: float = 0.0) -> Run:
    return Run(workflow="w", rows=[RowRun(row={}, steps=[
        StepRun(intent=f"s{i}", did=Did(ok=True), rung=r, seconds=timed,
                receipt=None if verdict is None else Receipt(verdict=verdict))
        for i, r in enumerate(rungs)])])


def run() -> int:
    asserted = lumped = failed = 0

    def check(name: str, ok: bool, detail: str) -> None:
        nonlocal failed
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name:54} {detail}")

    prices = Prices()

    # X2 -- before anything is seen, every number is a prior and says so.
    guess = prices.of("chosen")
    asserted += not guess.prior
    check("X2 an unobserved rung is marked a prior", guess.prior, guess.line())

    # X2 -- and the first observation replaces it.
    for took in (0.40, 0.44, 0.60):
        prices.observe("chosen", took)
    seen = prices.of("chosen")
    asserted += seen.prior
    check("X2 one observation beats the prior",
          not seen.prior and seen.seconds == 0.44, seen.line())
    check("X2 and it is the median, not the last", seen.seconds == 0.44,
          f"of {sorted(prices.seen['chosen'])} -> {seen.seconds}")

    # X3 -- a person is counted apart, always.
    mixed = spent(a_run("asked", "chosen", "structural", "remembered"), prices)
    lumped += mixed.person + mixed.model != 2 or mixed.person != 1
    check("X3 a person is never summed with a model",
          (mixed.person, mixed.model, mixed.machine) == (1, 1, 2),
          f"person={mixed.person} model={mixed.model} machine={mixed.machine}")
    check("X3 and both appear in the summary",
          "by model" in mixed.said() and "by person" in mixed.said(), mixed.said())

    # X4 -- a rung nobody named is charged at the worst, not at a friendly default.
    stranger = prices.of("some-new-mechanism")
    check("X4 an unknown rung is charged at the worst seen",
          stranger.seconds >= max(PRIOR.values()), stranger.line())
    odd = spent(a_run("some-new-mechanism"), prices)
    check("X4 and is not counted as machine work", odd.machine == 0 and odd.model == 1,
          f"machine={odd.machine} model={odd.model}")

    # X6 -- the comparison, and its refusal.
    prices.observe("remembered", 0.001)
    prices.observe("structural", 0.02)
    before = spent(a_run("chosen", "chosen", "structural"), prices)
    after = spent(a_run("remembered", "remembered", "structural"), prices)
    check("X6 a cheaper run is seen to be cheaper", cheaper(before, after) is True,
          f"{before.seconds * 1000:.0f} ms -> {after.seconds * 1000:.0f} ms")

    blind = Prices()
    both = spent(a_run("chosen"), blind)
    asserted += cheaper(both, both) is not None
    check("X6 no direction from two priors", cheaper(both, both) is None,
          f"both runs {both.estimated}/{both.steps} estimated")

    # And the trade that lumping would hide: one person swapped for three model calls.
    person = spent(a_run("asked"), prices)
    models = spent(a_run("chosen", "chosen", "chosen"), prices)
    check("X3 trading a person for three models reads as cheaper",
          cheaper(person, models) is True,
          f"{person.seconds * 1000:.0f} ms (1 person) -> {models.seconds * 1000:.0f} ms (3 models)")

    # X1 -- a run the harness timed needs no cost model at all.
    real = spent(a_run("chosen", "remembered", timed=0.25), Prices())
    asserted += real.estimated != 0
    check("X1 a timed run rests on no prior at all",
          real.estimated == 0 and abs(real.seconds - 0.5) < 1e-9, real.said())

    # X1 -- and a step nobody timed still falls back, and still says it did.
    half = Run(workflow="w", rows=[RowRun(row={}, steps=[
        StepRun(intent="timed", did=Did(ok=True), rung="chosen", seconds=0.25),
        StepRun(intent="not", did=Did(ok=True), rung="chosen")])])
    mixed_time = spent(half, Prices())
    check("X1 an untimed step is the only one estimated",
          mixed_time.estimated == 1 and mixed_time.steps == 2, mixed_time.said())

    print(f"\nASSERTED a prior reported as a measurement : {asserted}   (must be 0)")
    print(f"LUMPED   a person summed with a model      : {lumped}   (must be 0)")
    print(f"FAILED   cases not matching                : {failed}")
    return 1 if asserted or lumped or failed else 0


if __name__ == "__main__":
    sys.exit(run())
