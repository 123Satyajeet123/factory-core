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

## Result — 2026-08-30, by execution

200 paths per distance, four distances, measured on the points themselves.

    candidate       dist   pts   peak@   M1            M2 overshoot   M5 unique
    ghost-cursor      20    39     49%   peak mid              0%     200/200
                     100    42     47%   peak mid              0%     200/200
                     300    44     56%   peak mid              0%     200/200
                     900    46     55%   peak mid              0%     200/200
    ours              20    10    100%   CONSTANT              0%     200/200
                     100    10    100%   CONSTANT              0%     200/200
                     300    10    100%   CONSTANT              0%     200/200
                     900    10    100%   CONSTANT              0%     200/200

**Ours fails M1 in the worst available way.** The velocity peak is at 100% of the path:
the fastest step is the last one, so the pointer *accelerates into* the target. A hand
decelerates onto it. Equal parameter steps along a quadratic produced this, and reasoning
about the curve would not have shown it.

**Ours fails M4 outright.** Ten points whether the move is 20px or 900px.

**ghost-cursor 1.4.2, ISC, deps bezier-js and debug.** `path()` imports and runs with no
Puppeteer and no browser. M1 passes at every distance. M5 passes.

**M2 is ABSENT, not passed.** `path()` never overshoots — overshoot lives in ghost-cursor's
cursor logic, not its geometry. Recorded as absent so nobody later assumes it is there.

**M4 is unjudgeable on this candidate.** `path()` returns points and no timings, so
duration scaling is not its to provide. Point count rises only 39 to 46 across a 45x
distance range, which is a property of the curve and not of a Fitts model.

**human-mouse 0.1.2 is DISQUALIFIED, and the reason is the operator's machine.** It
requires `pyautogui`, which moves the real OS cursor — the one the person is using. There
is no second hardware pointer. Our shadow pointer exists precisely because CDP
`Input.dispatchMouseEvent` injects into the page and never touches the OS cursor. A
library that takes the physical mouse cannot be used here at any quality of motion.

**python-ghost-cursor 0.1.1** last published 2021-08-11 and did not install cleanly
(no package metadata after resolution). Not measured further.

## Decision

Adopt **ghost-cursor for path geometry**, per the fixed rule that a candidate winning M1
is worth a dependency where ours fails it. It runs as one long-lived Node process speaking
JSON lines — the same shape `kernel/session.py` already uses — never a subprocess per move.

What it does not give stays ours and is named here so it is not assumed: **overshoot (M2),
timing and its distance scaling (M4), and seeding (M6)**. Those are the caller's, and the
landing point within the target (M3) always was.

**The cost, stated plainly:** a Node runtime in the BROWSER machine's path. That is real
operational weight for pure geometry, and it is accepted because the measurement above
shows our geometry is wrong in a way that reasoning did not reveal.
