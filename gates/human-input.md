# Does a press arrive the way a hand delivers one?

Written **before** `hand.py` exists. What follows is what makes input look driven, stated
so it can be checked rather than believed.

## The claim being tested

`stealth.py` makes the browser look right; this makes the DRIVING look right, and they are
different problems. A real Chrome binary on a signed-in profile with a plain CDP attach
still produces, by default: a click with no pointer movement at all, a whole field typed
in one event, and the next act in the same millisecond. Nothing about the fingerprint is
wrong. No hand has ever produced that timing.

## What must hold

**H1 the pointer travels.** A press is preceded by `mouseMoved` events along a path, not a
single jump to the destination. Checked by counting the moves the page received before the
press, and that their positions differ.

**H2 the pointer arrives before it is measured.** Order is reach, then hit-test, then
press. Movement can change what is under a point — a hover menu is the ordinary case — and
a guard that measures before travelling would approve a target the pointer then leaves.
Checked by a fixture whose element moves on `mouseover`: the guard must refuse.

**H3 one point, three uses.** Travel, hit-test and press use the same number. Checked by
construction: the point is computed once and passed, never recomputed.

**H4 timing is drawn, not constant.** Dwell before pressing, and rest between acts, vary.
Checked by taking several samples and requiring they are not all equal.

**H5 reproducible when seeded.** The same seed gives the same path and the same delays, or
a failure cannot be re-run.

## What is deliberately NOT claimed

That this defeats any particular detector. Nothing here is measured against a live site,
and a pass is "input has the shape of a hand", never "we are undetectable". A claim about
a real site needs a measurement against a real site, and this is not one.

## Result — 2026-08-30

**H1 the pointer travels.** Yes, and the page counts it: 70 moves before a refusal on the
overlay case, 34 on the hover case, 18 on the off-viewport case. Zero moves appear only
where the target had no box to travel to, which is a refusal before travel rather than a
press without it.

**H2 the pointer arrives before it is measured.** Confirmed by the case built for it. The
skittish target moves away on `mouseover`; the guard travels, re-measures, finds `HTML`
under the point and sends nothing. Measuring before travelling would have approved it.

**H3 one point, three uses.** By construction: `hit.where` produces the point, and travel,
`hit.at_point` and dispatch all take that same value. There is no second computation to
disagree.

**H4 timing is drawn.** 400 draws, all distinct, and the mean sits above the median — the
defining property of the log-normal, where a uniform draw has them equal.

**H5 reproducible when seeded.** Same seed, same delays and same aim points.

**M3, which was not in this gate and should have been.** Every press used to land on the
exact pixel centre of its target. `Hand.aim` now draws the landing point, and the run
reports 20 distinct points out of 20.

**What this does not show.** No press was dispatched in the run, because the only case that
should have dispatched failed at locate. So the travel numbers are all from refusals. The
shape of a press that actually lands is still unmeasured.
