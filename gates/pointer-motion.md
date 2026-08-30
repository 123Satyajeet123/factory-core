# Whose motion model? Criteria fixed before reading any candidate.

Written **before** opening ghost-cursor, python-ghost-cursor or human_mouse. What follows
is measured on the OUTPUT of a path generator — a sequence of points and the delays
between them — so it applies to a library in any language and to ours equally.

## Why this is not ours to write

Path generation is pure geometry and has a maintained prior art. Writing our own is the
rung this project does not take. But a dependency has to earn the same way a vendor does,
so it is measured rather than adopted on a README.

## The current implementation's known tells, recorded as the baseline to beat

    every click lands on the exact pixel centre of its target
    delays drawn uniformly between two bounds
    equal steps along the curve, so velocity is constant
    no overshoot and no correction
    step count from a fixed range whether the move is 20px or 900px

## Criteria

**M1 velocity profile.** Speed must rise and fall across the move. Measured as the
inter-point distances along a path: their peak must lie away from both ends. FAIL if the
distances are near-constant, which is what equal parameter steps produce.

**M2 overshoot and correction.** Over longer distances some proportion of moves should
pass the target and come back. Measured as: does any point lie beyond the target along the
line of travel. A model that never overshoots is not disqualified, but it must be recorded
as absent rather than assumed present.

**M3 landing point varies.** Repeated moves to the same element must not land on the same
pixel. This may belong to the caller rather than the generator; whichever provides it, the
end-to-end behaviour is what is scored.

**M4 distance scaling.** A longer move must take more time and more points, and the
increase must be sublinear in distance — the Fitts relationship. Measured across at least
four distances spanning an order of magnitude.

**M5 non-repeating.** Two unseeded calls with identical endpoints must differ.

**M6 reproducible when seeded.** The same seed must give the same path, or a failing run
cannot be re-run. A candidate without a seed hook fails this and it is a real cost.

**M7 what it costs.** Maintenance signal, licence, dependency weight, and whether adopting
it drags in a browser driver we do not use. A path generator that requires Puppeteer to
produce a list of points is the wrong shape regardless of the quality of the points.

## Decision rule, fixed now

- Adopt per criterion, never wholesale. The generator and the landing-point choice are
  separate; a candidate can win M1/M2/M4 and lose M3 without that being a problem.
- A candidate that wins M1, M2 and M4 is worth a dependency even if it loses M5 and M6,
  provided M6 can be recovered by seeding the caller's own random source.
- If no candidate wins M1 or M4, keep ours and say plainly what it does not do rather than
  adopting something to have adopted something.

## What is deliberately NOT claimed

That any of this defeats a particular detector. Nothing here is measured against a live
site, and a pass means "the motion has the statistical shape of a hand", never "we are
undetectable". A claim about a real site needs a measurement against a real site.

## Result

(filled in by execution — not by reasoning)
