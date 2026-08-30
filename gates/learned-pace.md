# Can the hand be fitted to the person, from the ledger we already record?

Written **before** building any of it.

## The idea, and why it is not a small one

The factory watches a person work in order to learn a workflow. The same recording carries
something else, for free: **how that person drives a browser.** Their pointer paths, the
gaps between keystrokes, how long they rest on a control before pressing, where inside a
button they actually land.

Today `Hand` moves the way ghost-cursor's geometry and my chosen distributions say a
generic person moves. That is a model of nobody. The operator's own recording is a model of
the one human whose machine this is, and it costs nothing extra to collect because
`record.py` is already listening.

**The principle is the same one the FACTORY runs on.** A capability comes from the record,
never from an idea about what the procedure might be. A pace should come from the record
too, never from a constant I picked.

## Why this is the right channel and not a clever trick

What a page can measure about driving is exactly what our recorder can measure: `mousemove`
positions and their timing, `keydown` intervals, the delay between arriving at a control
and pressing it. We are fitting to the same signal a detector reads, on the same channel,
from the same person on the same machine. Nothing is being guessed at.

## Criteria

**P1 it fits from real events, not from a questionnaire.** Parameters are estimated from
recorded pointer and key events. If a run has no recording, the defaults stand.

**P2 it fits per person, and per machine.** Trackpad and mouse produce different
distributions and so do different people. The fit is scoped, and the scope is the operator.

**P3 it degrades honestly.** Too few samples must leave the defaults in place rather than
fit noise. The number of samples behind a fitted parameter is recorded with it.

**P4 nothing recorded is a keystroke's CONTENT.** Timing, not text. A pace model that
stores what was typed is a password store, and this project does not hold those.

**P5 it is measurable against the generic model.** The fitted pace must be comparable to
the default on the same statistics used in `gates/pointer-motion.md` — velocity profile,
overshoot rate, dwell distribution — so "fitted" can be shown to differ rather than
asserted to be better.

**P6 it stays a `Pace`.** The output is the same object `Hand` already takes. If fitting
requires a new mechanism inside `Hand`, the fit is doing too much.

## Where it lives, and how everything converges on the driver

    browser/record.py   already listening. Adds pointer and key TIMING to what it keeps.
    browser/pace.py     fits a Pace from those events.        <- new, small
    memory/             holds the fitted Pace at operator scope, promoted like anything
                        else: it is evidence, and a fit from twelve samples should not
                        outrank one from twelve hundred.
    browser/hand.py     takes the Pace it is given. Unchanged.
    browser/machine.py  the driver holds the Hand. Unchanged.

So the driver is where it lands, and nothing above the driver learns that any of this
happened.

## What would make this dishonest

Fitting to a recording made while the factory itself was driving. That is the system
learning to imitate itself, and the distribution would converge on whatever we already do.
Only segments a PERSON produced may be fitted from, and the ledger already knows which are
which because taking the wheel writes a segment.

## Result

(filled in by execution — not by reasoning)
