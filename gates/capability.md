# What a candidate must pass, and what was measured getting there

The CAPABILITY line is seven gates in one order. This file holds what was measured building
them, so the code does not have to carry it — a finding is dated here and reloads on nobody's
every read.

    worth -> draft -> discriminate:reading -> publish -> offer -> discriminate:behaviour -> prove

## Why this order

`worth` is first because it is the only gate answerable without doing any work. Drafting,
publishing and installing a stock interaction all succeed, and the library is worse for it.

`prove` is last because it is the only one that can say the capability did anything, and it
is the one most candidates will sit at: proving needs a reader that can address the
destination, and there is one.

## worth — the threshold is measured, not picked

`difflib.SequenceMatcher` over step signatures, values excluded. The pairs produced the gap
the threshold sits in:

    identical              1.000     the same procedure
    one step added         0.889     the same procedure, varied
    one step dropped       0.857     the same procedure, varied
    ------------------------------   SAME = 0.85
    one field renamed      0.750     a DIFFERENT field: a different procedure
    a different tail       0.571
    nothing in common      0.000

**A different target name is a different procedure**, and that is the decision the number
encodes. Writing into `Body` rather than `Note` is not a variation of one capability; merging
them gives a chooser one entry that does two things. What IS a variation is the same targets
with a step more or less.

Values are excluded from the shape on purpose: the same procedure with different arguments is
one capability, or a library fills with one entry per row of a spreadsheet.

## publish and offer — the vendor's contract, read at the pinned revision

`prime-agent/packages/coding-agent/skills/skill-creator/references/python-skills.md`:

- `SKILL.md`, `pyproject.toml` at the root, and `src/<import_name>/__init__.py`. All three,
  or the skill silently degrades to markdown-only with a load warning, and the name is bound
  to a placeholder that raises only when called. **A capability that loaded as prose looks
  installed**, which is why `offer` refuses an incomplete layout rather than warning.
- The import name is the skill name with hyphens as underscores, and hatchling needs
  `packages = ["src/<import_name>"]` because the project name and the directory always differ.
- `prime-agent-runtime` is never declared as a dependency: it is bundled rather than
  published, so declaring it breaks the install everywhere except the kernel venv.

**`await name(...)` is not available to us, measured.** The reference says the kernel "wraps
the module so the module itself is an async callable" — that wrapping lives in prime-agent's
TypeScript host. `rlm.skill` ships only `cli`/`run_cli`. A plain import gives
`TypeError: 'module' object is not callable`; the documented equivalent `await name.run(...)`
works. Same cause for the docstring and signature being copied onto the module: they survive
on `run` itself, and they matter because the vendor's contract makes them the capability's
API *and* its CLI help.

**Installed means importable after a cache refresh.** `uv pip install -e` returned 0 and the
next cell raised `ModuleNotFoundError`: an editable install adds a `sys.path` entry through a
`.pth` that `site` reads at interpreter startup, and a kernel that was already running does
not see one.

## discriminate — reproduction is an inverted filter

Measured in a prior tree: admitting a capability because it reproduced its recorded output
passed 16 of 103 candidates, and **every survivor was a file read**. A command that does real
work cannot reproduce byte for byte; one that does nothing reproduces perfectly.

Two checks that fail differently. A parameter never mentioned in the body is a procedure
ignoring its arguments, visible by reading. A parameter that IS mentioned may still thread
into nothing that leaves the process, which only sending it can show — so `varied` stays
`None` until something ran, and **a static pass alone is not a pass**.

Comparison is on what was SENT, never on what came back: a destination that answers the same
to everything would otherwise read as a capability ignoring its arguments, and those are not
the same defect.

## variations — "in parallel" is not available, and the reason is the vendor's

ReUseIt reports 24.2% to 70.1% by running variations in parallel and mining failures as well
as successes. The mining is adopted. The parallelism is not, and this is why:

`rlm/repl.md` — *requests other than `interrupt` and `host_reply` run strictly in order, one
at a time*. So fan-out cannot happen by sending several cells; it would have to happen inside
one, where the runtime's own loop can host concurrent tasks. And the actuator is one browser
on one page, which serialises regardless. `at_once` exists for a destination that can take it
and defaults to one because ours cannot.

## failures — a guard separates, or it is not a guard

A condition every failure showed and no success did. One present in both is a coincidence
with a good story, and adding it makes the capability refuse work it could have done.

**With no attempt that held, there is nothing to separate from.** Every condition is then
simply what this capability always does, and emitting it produces a capability guarding
against being itself. That is `always_fails`, and it is a reason to refuse the whole
candidate rather than to guard. Found by execution: the first version emitted a guard for a
procedure that never once worked.

## amortize — the unit, and what it may never be summed with

EvoClawBench: end-to-end token efficiency 0.38 and 0.30. Skill workflows cost MORE than
direct execution once authoring was counted, and neither recovered without many reuses; the
ablation found empty scaffolds beating real skills, so the gain was a context reset.

The unit is a step that needed reasoning, priced by `observe.py`. **A person is never summed
with a model** — see `gates/cost-model.md`; the summed version made trading one person for
three model calls look three times worse.

Never recovering is the ordinary case, so `breakeven` says None rather than a large number.
A large number invites waiting for it.

Nothing is retired on silence: a capability nobody used has not failed to pay, it has not
been asked. And retiring is not deleting — what it cost and what it returned is the evidence
it was a bad candidate, and dropping that is how the same one gets drafted again next week.

## evidence — one reader, one unit

`memory/confidence.py` puts a Wilson bound on receipt counts, so `n` has to be honest. Five
receipts from one reader on one act is one observation; counting five narrows the interval on
evidence that was never independent.

Two readers disagreeing is kept as one confirmation and one refutation, not resolved. Picking
a winner is a judgement, and the bound already handles contradiction by moving down.

## draft — the procedure is read out of the record

SkillsBench, 7,308 trajectories: curated skills +16.2pp, self-generated ones about zero. A
model cannot reliably author the procedural knowledge it benefits from consuming. So the
steps come from a Workflow the compiler induced and a Run that actually happened, and the
only thing anyone asks a model for is a name.

Parameters are not re-derived: `compile/induce.py` already found what varied. Deriving them
twice is two mechanisms disagreeing the first time induction changes.

A cell acts through the door and nowhere else, so a published capability inherits the guard,
the pacing and the witness by construction — it could not reach raw CDP if it tried.

## notice — the unit is the sitting

Measured in a prior tree: twenty runs inside one afternoon is one experiment. Somebody trying
a thing until it works produces a burst of near-identical demonstrations, and treating that
burst as corroboration manufactures a capability out of ten minutes.

Only what a person did counts. A segment the factory drove is the system corroborating
itself, which is how a mistake becomes a habit.

## Result

Every gate above has an eval and every eval is in `evals/test_suites.py`. The code carries
none of this text; that is deliberate, and this file is where it was moved to.
