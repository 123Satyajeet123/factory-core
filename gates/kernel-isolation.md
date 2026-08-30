# What separates a cell from us, and does it need its own interpreter?

Written **before** `kernel/` holds code. `gates/kernel-browser-wire.md` settled how a cell
reaches a page; this settles what a cell can reach *otherwise*.

## Why this reopens

`kernel/venv.py` gave one reason for a second interpreter: *"prime-agent needs mcp>=2,
browser-use pins mcp==1.28.1 — the two cannot share a venv."* browser-use stopped being the
spine on 2026-08-30 and is tier 4, so that sentence is about a dependency we no longer have.

The conflict is real and it moved, measured today:

    candidates/prime-agent/prime-agent-runtime/pyproject.toml   mcp>=2,<3
    our venv                                                    mcp 1.26.0

`browser/serve.py` builds its door on `mcp.server.fastmcp` and `door_eval` drives it with
`mcp.client.streamable_http`, both on 1.26.0. So the incompatibility is now **ours against
prime-agent**, not a vendor against a vendor. Same conclusion, different reason, and the
reason is worth correcting because a stale one stops being checked.

**A reason that survives either way, and is the stronger of the two:** a cell is
model-written code. If it shares an interpreter with the factory it shares the factory's
imports, its open database handle, and its environment — and the environment is where the
keys are. A dependency conflict can be resolved by a version bump. That cannot.

## What is already established, so it is not re-litigated

- **Protocol 3, read from `rlm/repl.md` at the pinned rev.** `python -m rlm.repl`,
  newline-delimited JSON, one object per line. Requests on fd 0; events on a private dup of
  the original fd 1 taken before anything else runs, so protocol framing cannot be corrupted
  by user output. `ready` is the handshake. Exactly one `done` per id'd request, always
  after that request's other events.
- **Cells compile with `PyCF_ALLOW_TOP_LEVEL_AWAIT`** and run as tasks on one persistent
  loop, so `await` works at top level and a background task created by a cell keeps running
  between cells. That is a feature to test, not an accident to guard against.
- **Interrupt is delivered by SIGINT to the main thread**, and a request stays
  interrupt-targetable until its `done`. Interrupts for finished or unknown requests are
  dropped, and when nothing is running they are ignored.
- **The door is HTTP, and `rlm.mcp` speaks it.** `_open_transport` dispatches on
  `kind == "http"` to `_resolve_streamable_http` with a `url`; `browser/serve.py` serves
  streamable HTTP on loopback deliberately. The two sides already fit.

## Criteria

**K1 a cell cannot read a secret.** With the factory's own environment carrying an API key,
a cell asking for it gets nothing. Measured by executing the lookup in a cell, not by
reading the spawn code — an env that is scrubbed in one place and inherited in another
looks identical from the call site.

**K2 a cell cannot import the factory.** `import factory` from a cell fails. If it
succeeds, the cell can reach the browser without the door, and every guarantee the door
makes becomes optional.

**K3 top-level await works, and a background task survives the cell that made it.** Both
are load-bearing for the kernel as a *context* mechanism: a cell that cannot await cannot
query a large object held in the namespace.

**K4 an interrupt lands, and the runtime keeps serving.** After interrupting a running
cell, the next cell must execute normally. A kernel that has to be restarted to recover has
no interrupt.

**K5 a hung cell is bounded by us, not by hope.** A cell that never returns must not hold a
run open forever. The timeout is ours and the recovery path is `interrupt` — measured, with
the cost of recovery reported, because a timeout that leaves the kernel unusable is a leak
with a nicer name.

**K6 what a round trip costs.** One trivial cell, measured. `door_eval` put the browser
wire at 3ms against a 1116ms guarded act; the kernel's own wire has no such number yet and
`kernel-browser-wire.md` has been carrying it as an open item.

## Decision rule, fixed now

- If K1 and K2 can be met in one interpreter, the second venv is a cost with no buyer and
  is deleted. They almost certainly cannot, which is why they are written as criteria rather
  than assumed.
- The `mcp` version conflict is **not** a criterion. It is today's arithmetic and it would
  evaporate on a version bump; a decision resting on it would have to be re-made every time
  a pin moves.

## What is deliberately NOT claimed

That a separate interpreter is a sandbox. A cell still runs as our user, on our disk, with
our network. It cannot read our keys or import our code, and that is the whole of the
claim — anything stronger needs a container and is a different gate.

## Result — 2026-08-30, by execution

    runtime python 3.13.5, protocol 3

    K1 no secret reaches a cell        cell saw (None, None)
    K2 the factory is not importable   ModuleNotFoundError
    K3 top-level await                 result='awaited'
    K3 a task survives its cell        result=True
    K4 an interrupt lands              KeyboardInterrupt after 2.0s
    K4 the runtime keeps serving       next cell -> 'still here'
    K5 a hung cell is bounded          KeyboardInterrupt after 2.0s
    K5 and recoverable                 next cell -> 'recovered'
    K6 round trip                      0.3 ms median over 5 trivial cells

    ESCAPED 0    WEDGED 0

**Settled: two interpreters, on K1 and K2 rather than on `mcp`.** The environment handed to
a cell is an allowlist — `PATH HOME LANG LC_ALL TMPDIR TERM`, plus an emptied `PYTHONPATH`
— and a canary planted in the parent is invisible from inside a cell. That is the whole of
the isolation claim and it does not depend on any pin.

**K5 does not interrupt the way K4 does, and the difference is the runtime's.** A cell
suspended at an `await` cannot be reached by SIGINT — raising there would land in the wrong
task — so the runtime cancels the cell task and reports the cancellation as a
`KeyboardInterrupt`. Both paths end in `error` + `done` and both leave the session usable,
which is what K5 asks. Worth knowing before someone writes a cell that catches
`KeyboardInterrupt` around an `await`: it will not intercept this.

**K6, and the wire is not where the money goes.** 0.3 ms per round trip against
`door_eval`'s 1116 ms for one guarded browser act. Together with the door's 3 ms of wire,
`gates/kernel-browser-wire.md`'s open item — *the round-trip cost of one act over the
wire* — is answered: transport is under half a percent of an act, and pacing is the rest.

**The isolation checks were verified by breaking them.** `evals/mutation.py` now carries
two kernel mutations — a cell inheriting `os.environ`, and the repository placed on a
cell's `PYTHONPATH` — and both are caught.

**And the harness had the defect it exists to detect.** `noticed()` called each suite's
`run()` without awaiting it; the kernel suite's is a coroutine function, so `run() != 0`
compared a coroutine object to zero and was always true. Both kernel mutations reported
*caught* while the suite never executed. Found by a `RuntimeWarning`, not by the harness.
Fixed, and the harness was then checked in the other direction — a mutation of a constant no
case depends on is reported as SURVIVED, so a green run is falsifiable.
