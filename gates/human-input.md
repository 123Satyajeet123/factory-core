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

## Result

(filled in by execution — not by reasoning)
