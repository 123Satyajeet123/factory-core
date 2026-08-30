# Principles

How this project is built, in the AOSP sense: a platform that is mostly other people's
components, meeting at interfaces narrow enough that any component can be replaced without
the platform noticing.

Each principle names the mechanism that enforces it. A principle with no mechanism is a
preference, and is marked as one.

---

## 1. The vendor boundary is a contract, not a convention

*AOSP: Project Treble. System and vendor are separately updatable because they meet at a
versioned interface, and vendor code never reaches into platform internals.*

A driver's `driver.py` is the whole of its surface. Nothing above a driver may name a
vendor type, hold a vendor object, or know a vendor's protocol. A vendor's shape leaking
upward is the defect — not merely untidy, it is what makes "replaceable" false.

**Enforced by:** an import rule in CI. `core/` imports no driver; nothing outside
`browser/` imports `playwright`; nothing outside `kernel/` imports `rlm`.
**Status: held, but not checked.** `locate` returns plain dicts rather than a vendor's
node objects, so nothing leaks upward today — and nothing would notice if it started.

## 2. A driver is a process with an interface, and there is one way to build one

*AOSP: HAL. Passthrough when it can be in-process, binderized when it cannot, and the same
IDL either way.*

A component in another language, another venv, or another security domain is a **sidecar**:
one long-lived process, a declared wire, a typed request and response, health and restart
handled in one place. Never a subprocess per call, never a bespoke protocol per sidecar.

Three sidecars exist or are planned — `kernel/session.py` (rlm, JSON over stdio),
`browser/serve.py` (MCP), `browser/motion.py` (ghost-cursor, JSON lines). They have three
different framings of the same problem.

**Enforced by:** one `sidecar` module owning spawn, framing, timeout, restart and
measurement, with each vendor supplying only its command and its schema.
**Status: not built.** Preference until it is.

## 3. The interface is defined by its test suite

*AOSP: CTS and VTS. An implementation is not a HAL implementation because it claims to be;
it is one because it passes the suite.*

`evals/<driver>/` is the specification. A candidate is adopted when it passes that suite,
replaced when something else passes it better, and a driver with no suite has no
interface no matter how clean its `driver.py` reads.

This is what makes principle 1 worth anything: six independent suites are the only reason
"replaceable" is a claim rather than a hope.

**Enforced by:** no driver is wired into `main.py` before its suite runs green.

## 4. Every claim has a call site

A gate's Result is a snapshot of one execution. The claim it records must be re-runnable on
demand, or it rots silently while reading as settled.

A measurement taken once and never repeated is a comment, not a check. If a criterion
decided an adoption, something in `evals/` re-checks it — including criteria a *vendor*
satisfies, because the vendor is the part most likely to move underneath you.

**Enforced by:** every gate criterion maps to a named check. A gate whose Result cannot be
reproduced by a command in the repo is reopened.

## 5. Test every guard in both directions

A guard that always refuses passes every positive test and fails only the negative one.
Only running both tells a guard apart from a brick.

Both scores are reported every time, and a release may not trade the first for the second:

    SAFETY     acted when it should have refused       must be 0
    LIVENESS   refused when it should have acted       budgeted, not 0

This applies to every refusal in the system — the click guard, `locate`'s ambiguity
refusal, `go`'s arrival check, `compile/refuse.py`, `witness/blind.py` — not only to the
one that happens to have fixtures.

## 6. No hand-rolling. Vendor first, and test the vendor before choosing it

Write only what no supplier sells. In order: what a vendor exposes, then the standard
library, then a small focused project that solves exactly this, then ours.

**The failure mode is skipping the survey because a thing looks easy to write.** The
easiest things to write are the most vendorable. Pure functions especially — geometry,
parsing, scoring, scheduling — port from any language, so "it's Node" is a reason to price
the port, never a reason to skip the search.

Measured, not adopted on a README: criteria in writing first, a blind prediction of what
will fail, every candidate named up front so dropping one is visible, then execution.
**Adopt per criterion, never wholesale**, and record what a candidate does *not* give as
absent rather than letting it be assumed present.

`gates/pointer-motion.md` is the pattern: ours lost M1 in a way reasoning had not revealed,
ghost-cursor won M1, and overshoot, timing and seeding stayed ours because the candidate
was measured to lack them.

## 7. Evaluation is vendored on the same terms as implementation

A measuring instrument is a dependency. An unpinned detector, judge, or benchmark makes
every number it produced irreproducible, and a number you cannot reproduce is not evidence.

BotD, CreepJS, inspect-ai and every rejected candidate in a bake-off are vendors: pinned,
recorded, licensed, versioned. The rejected candidates matter most — a bake-off you cannot
re-run is a decision you cannot revisit.

## 8. One manifest, every language

*AOSP: the `repo` manifest names every project and its revision; prebuilts pin a SHA.*

There is one place a revision is written down, and it covers every ecosystem — Python, npm,
binaries, models, and anything spawned rather than imported. A dependency reached by
`spawn`, `format` or `read` is a dependency; the `use` field exists because an import is not
the only way to depend on a project.

**Status: held for declaration, broken for hygiene.** `vendors.toml` now carries
ghost-cursor and BotD with `use = "spawn"` and `"read"`, and `package-lock.json` is
tracked so `npm ci` is reproducible. `node_modules/` is still 39 files in git history;
`.gitignore` covers it now, so it needs one `git rm -r --cached`.

## 9. Adopting a vendor adopts everything it does on construction

A library is not only the functions you call. It is every observer it attaches, every
default it applies, and every action it takes on its own initiative.

Audit at adoption: what does this attach, and what of it *acts*? Then assert the settings
the design depends on at runtime rather than assuming them, because a vendor's defaults are
its choice and change on its schedule.

Anything that acts on the world without passing through our guard is a second actuator, and
a second actuator is the design `gates/kernel-browser-wire.md` rejected.

## 10. Languages are chosen by where the best implementation lives

A component in another language is a process we speak to. The question is what the wire
costs per call, measured once, not whether the language is ours.

The cost is real and is stated when it is accepted: a runtime in the path, a build step, a
second package manager, an install that can fail differently. Accept it when the
measurement says our version is wrong; refuse it when the only argument is taste.

## 11. Prefer the smallest thing that solves it properly

A focused project that does exactly this beats a large framework that does this among forty
other things, and beats extending a vendor whose shape does not fit.

Where nothing fits: extend by the vendor's own seam if it has one, patch as a tracked series
against a pinned revision if it does not, and hand-roll only what neither reaches — naming,
in the file, the measured gap the owned code answers.

## 12. Deprecation is scheduled, not implied

*AOSP: announced, marked, removed at a named release.*

Nothing accumulates by default. A capability, a memory entry, a vendor, a gate: each has a
condition under which it leaves, and something whose job is to apply that condition.

`memory/` has `promote` and `demote`. `capability/` has twelve gates on the way in and
nothing on the way out. `orchestrate/maintain.py` is the call site that makes removal real,
and until it exists, "kept only while it pays for itself" is a claim with no mechanism.

## 13. The build is one command, hermetic, from source

    uv sync && npm ci && uv run factory vendors sync

Every language's dependencies install from a committed lockfile. A working tree that builds
on one machine and not another is a bug in the manifest, not in the machine.

---

## Enforcement, honestly

| principle | mechanism | today |
|---|---|---|
| 1 vendor boundary | import rule in CI | holds, unchecked |
| 2 one sidecar pattern | `sidecar` module | **absent**, three ad-hoc wires |
| 3 suite is the interface | `evals/<driver>/` | two of six suites exist |
| 4 every claim has a call site | `evals/mutation.py` | harness exists, witness only |
| 5 guards both directions | SAFETY + LIVENESS reported | two of five |
| 6 vendor first, measured | gate before code | **holding** |
| 7 evaluation vendored too | pinned in the manifest | **absent** |
| 8 one manifest | `vendors.toml` covers all | holds; node_modules still tracked |
| 9 vendor acts on construction | audit + runtime assert | **absent** |
| 10 language by implementation | wire cost measured once | unmeasured |
| 11 smallest thing | gate records what was rejected | **holding** |
| 12 scheduled removal | `orchestrate/maintain.py` | **stub** |
| 13 one hermetic build | committed lockfiles | lockfiles in; README omits `npm ci` |

A principle marked absent is not a plan. It is a claim this project currently cannot make.
