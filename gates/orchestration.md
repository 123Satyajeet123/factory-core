# What starts a run when nobody is watching, and who is allowed to?

Written **before** a line of `orchestrate/` beyond `maintain.py`, and before reading any
candidate. `apscheduler` has been declared in `pyproject.toml` since the first commit and
imported by nothing — the same shape `gates/model-vendor.md` just found with litellm and
instructor, and it is being opened for the same reason: a declared vendor is a prediction.

## The question that actually decides this

Principle 9: *adopting a vendor adopts everything it does on construction, and anything
that acts on the world without passing through our guard is a second actuator.*

A scheduler's entire purpose is to act on its own initiative. That is not an incidental
side effect to audit — it is the product. So the question is not "which scheduler" but
**whether a scheduler is the right shape at all**, when what this system needs might be a
predicate — `is this workflow due?` — that something else asks.

The difference is not stylistic. A scheduler owns a thread, a clock and a job store, and it
fires callables it deserialised. A predicate owns nothing and fires nothing. One of those
can start an irreversible workflow at 3am while nobody is at the keyboard; the other cannot
do anything at all.

## What is already true, so it is not re-litigated

- **`run/stop.py` bounds a run from inside**: a cap code owns, a goal the work declares, a
  refutation, and grinding. Nothing here may raise any of them.
- **`authority/permit.py` bounds what a run may do**: no permit, no irreversible act, and
  an unattended run cannot grant itself one. This gate must not create a way around that.
- **`store/db.py` is a sqlite database with WAL** and already holds entries, questions and
  permits. A lease is a row.
- **`maintain.sweep` exists and has no caller.** Whatever runs on a cadence has to run it,
  or promotion stays a pass nobody makes.

## Criteria

**O1 due, without owning a clock.** Can the candidate answer "is this due, given the last
run and a cadence" as a function, without starting a thread, a loop or a process? A library
that can only be used by handing it a callable has failed this.

**O2 one runner, and a dead one lets go.** Two runs of one workflow at once is two browsers
driving one page. A lease must be exclusive AND expire — a runner killed mid-row must not
hold a workflow forever. Measured by killing one.

**O3 nothing fires without a person, at first.** A newly scheduled workflow must not run
unattended until somebody has said it may. Permits already gate the irreversible steps;
this is about the run existing at all.

**O4 the cadence is data, not code.** A workflow's schedule is per workflow, stored, and
editable without a deploy — the same argument `authority/question.py` makes for answers.

**O5 what it costs to adopt, stated.** Threads started, files written, signals installed,
atexit hooks, and anything it does at import. Principle 9 is a measurement here, not a
sentiment.

**O6 misfire is a decision we make.** A machine asleep for six hours wakes owing six runs.
Running all six, running one, or running none are three different answers and the system
has to pick — a vendor default picked for us is the failure.

## Candidates, named up front so dropping one is visible

- **apscheduler** — declared already, never imported. v4 and v3 differ enough to count as
  two candidates; whichever is installed is the one measured.
- **the standard library** — `datetime` for due, a sqlite row for the lease, and the OS for
  the cadence.
- **the OS** — launchd, systemd timers, cron. The cadence leaves the program entirely.
- **celery / dramatiq / arq** — task queues. Named so dropping them is visible; a broker
  for one machine's browser is principle 11's failure.
- **`schedule`** — the pypi package. Loop-driven, in-process.

## Blind prediction, recorded before measuring

Almost all of this is `datetime` and one sqlite table. apscheduler loses O1 because its
value is the thing we do not want — it owns the firing — and O5 will show a thread pool and
an atexit hook it installs for us. The OS wins the cadence, because a machine that was
asleep is the OS's problem and it already solved it. What stays ours is the lease and the
due predicate, which together are under a hundred lines.

If that prediction is right, `apscheduler` comes out of `pyproject.toml` and this driver is
ours — and the honest version of that is that `orchestrate/` was never a driver, because
there is no vendor behind it.

## Decision rule, fixed now

- A candidate that cannot be used as a predicate is not adopted, whatever else it does.
- Adopt per criterion: the cadence, the lease and the due test may have different answers.
- If the standard library wins outright, `apscheduler` is removed from the manifest rather
  than left declared, because a dependency nobody imports is what this gate exists to catch.

## Result — 2026-08-30, by execution. The prediction was WRONG on O1.

    O1  CronTrigger.from_crontab("0 9 * * *").get_next_fire_time(previous, now)
        -> 2026-08-30 09:00+00:00 with no previous fire
        -> 2026-08-31 09:00+00:00 given a previous fire at 09:00
        threads after import and use: 1 (before import: 1)

**A trigger is a pure function.** The prediction said apscheduler loses O1 because its
value is the firing. Half of that was wrong: the *triggers* own no clock, start no thread
and fire nothing. Cron parsing with timezones and DST is genuinely hard and thoroughly
vendorable, and it is available here without adopting anything that acts.

    O5  import apscheduler                    threads 1 -> 1
        BackgroundScheduler()                 threads 1 -> 1
        .start()                              threads 1 -> 2, running=True
        .shutdown(wait=True)                  threads 2 -> 1

The thread arrives at `.start()`, not at import or construction. So the two halves are
cleanly separable, which is what makes adopting one of them possible.

    O6  job_defaults: {'misfire_grace_time': 1, 'coalesce': True, 'max_instances': 1}

**This is the finding that decides the firing half.** A machine asleep for six hours wakes
owing six runs. `coalesce=True` collapses them to one, and `misfire_grace_time=1` then
drops that one for being more than a second late. The default answer is *silently run
nothing*, and it was chosen by the vendor. O6 says a default picked for us is the failure,
and this is exactly that — not because it is the wrong answer, but because nobody here
decided it.

### Adopted, per criterion

    cadence expression + due     apscheduler triggers, as pure functions.  ADOPTED
    firing, threads, job store   not adopted. Nothing starts a run but a person or the OS.
    misfire policy               ours, and explicit, because the default drops runs.
    lease                        ours. One row, exclusive, expiring.
    cadence storage              ours. Data per workflow, not code.

`apscheduler` stays in the manifest, at tier 1, `use = "import"` — but for the half that
computes rather than the half that acts. That distinction is the whole result.

### What this means for the shape

`orchestrate/` is not a driver. There is no vendor behind it to replace, only a function
borrowed from one. It is a line, like `compile/` and `run/`.
