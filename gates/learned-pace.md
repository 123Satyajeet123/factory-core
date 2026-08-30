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
    browser/driver.py   the driver holds the Hand. Unchanged.

So the driver is where it lands, and nothing above the driver learns that any of this
happened.

## What would make this dishonest

Fitting to a recording made while the factory itself was driving. That is the system
learning to imitate itself, and the distribution would converge on whatever we already do.
Only segments a PERSON produced may be fitted from, and the ledger already knows which are
which because taking the wheel writes a segment.

## Result — 2026-08-30, the recorder and the fit, not yet a person

    recorder saw   moves=303  keys=10  presses=6  releases=6
    landing points 6 distinct of 6
    fit samples    keystroke=9 press=6 rest=5 dwell=6 aim_spread=12 travel=3
    kept default   keystroke, press, rest, dwell, travel

**P3 holds, and this run is mostly P3.** Every parameter with fewer than twelve
observations kept its default and said so. Only `aim_spread` reached the threshold. A fit
that reported numbers for all six here would have been fitting noise and calling it
knowledge.

**P1 holds on synthetic events** (`python -m factory.browser.pace`): 199 keystroke gaps, 60
holds and 120 landing points produce a pace measurably unlike the default, and a thin
recording leaves the default alone.

**THE RECORDER CAUGHT A DEFECT IN OUR OWN DRIVER, WHICH IS THE POINT OF BUILDING IT.**
First run: `keys=0` after typing ten characters. `Input.dispatchKeyEvent` with `type: char`
fires `keypress` and `input` and never `keydown` — so text appeared with no keystrokes
behind it, which is precisely what a behavioural detector looks for. Fixed to keyDown, char,
keyUp; the recorder now sees ten. Nothing else in the tree would have found this, because
the recorder is the only thing reading the same channel a detector reads.

**Not yet done, and it is the whole point: no fit from a person exists.** These events came
from our own hand, which `gates/learned-pace.md` forbids fitting from — the distribution
would converge on whatever we already do. What is verified is the recorder, the fit, and
the honest degradation. The fit itself is unproven until a person demonstrates something.

**P2 now has a home, and the round trip runs.** `memory/` holds three tiers with
inheritance down and elevation up, and the fitted pace lives at MAIN under one key, because
how somebody drives a browser belongs to them and their machine rather than to any task:

    main: pace fitted from 199 gaps, kept at MAIN, recalled as (0.255, 0.353)

The default is `(0.05, 0.16)`, so what came back is the fit and not the constant.
`factory/main.py` is the only module that knows both machines exist; `browser/pace.py`
imports no memory and `memory/` imports no browser.
