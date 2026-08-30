"""Is a drafted capability read out of the record, and does it refuse when the record is thin?

    uv run python -m evals.capability.draft_eval

No browser and no site. The Workflow and the Run are the shapes `compile/` and `run/`
produce; what is checked is that a procedure comes out of them with no model asked, that it
acts only through the door, and that a run nobody watched succeed produces nothing.

    INVENTED   something in the body came from nowhere in the record   must be 0
    CREDULOUS  a capability was drafted from a run that did not work   must be 0
"""

from __future__ import annotations

import ast
import sys
import tempfile
from pathlib import Path

from factory.capability.draft import NotDrafted, draft, worked
from factory.capability.publish import complete, write
from factory.core.evidence import Did, RowRun, Run, StepRun
from factory.core.verbs import Doing
from factory.core.workflow import Step, Target, Workflow

WORKFLOW = Workflow(
    name="file-a-note",
    params=("note",),
    steps=[
        Step(doing=Doing.GO, intent="open the form", value="http://127.0.0.1:8088/form.html"),
        Step(doing=Doing.WRITE, intent="write the note", param="note",
             target=Target(role="textbox", name="Note")),
        Step(doing=Doing.PRESS, intent="submit", target=Target(role="button", name="Save")),
    ],
)


def a_run(*, held: bool) -> Run:
    """One row. `held` decides whether every step reported ok, which is the only thing
    `worked()` may look at -- a row that stopped is not evidence of a procedure."""
    steps = [StepRun(intent=s.intent, did=Did(ok=held or i == 0, detail=s.intent))
             for i, s in enumerate(WORKFLOW.steps)]
    return Run(workflow=WORKFLOW.name, rows=[RowRun(row={"note": "hello"}, steps=steps)])


def run() -> int:
    invented = credulous = failed = 0

    def check(name: str, ok: bool, detail: str) -> None:
        nonlocal failed
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name:46} {detail}")

    it = draft(WORKFLOW, a_run(held=True))

    # D1 -- it is Python, and its signature is the workflow's parameters.
    tree = ast.parse(it.body)
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef)
              and n.name == "run")
    args = [a.arg for a in fn.args.args]
    check("D1 the signature is the diff", args == list(WORKFLOW.params), f"run({', '.join(args)})")

    # D2 -- every literal in the body traces to the workflow. Nothing invented.
    known = {s.value for s in WORKFLOW.steps} | {
        t for s in WORKFLOW.steps if s.target for t in (s.target.role, s.target.name)}
    strings = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant)
               and isinstance(n.value, str) and len(n.value) > 2}
    #: The door's own verb names and the server name are ours, not the workflow's.
    ours = {"browser", "click", "write", "ok", "done"}
    stray = {s for s in strings if s not in known and s not in ours and " " not in s
             and not s.startswith(('"', "Drafted", "Every", "Returns"))}
    invented += len(stray)
    check("D2 no literal comes from nowhere", not stray, f"stray={sorted(stray) or 'none'}")

    # D3 -- it reaches the page only through the door.
    calls = {n.func.attr for n in ast.walk(tree)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    check("D3 the door is the only way out", calls == {"call_tool", "append", "get"},
          f"calls {sorted(calls)}")
    check("D3 and raw CDP is not reachable", "cdp" not in it.body.lower(), "no cdp in body")

    # D4 -- a run where a step did not hold is not evidence.
    check("D4 a stopped row is not a completed one", not worked(a_run(held=False)),
          f"worked()={worked(a_run(held=False))}")
    drafted = True
    try:
        draft(WORKFLOW, a_run(held=False))
    except NotDrafted as why:
        drafted, reason = False, str(why)
    credulous += drafted
    check("D4 and drafting from it is refused", not drafted,
          reason if not drafted else "DRAFTED IT ANYWAY")

    # D5 -- what comes out is what `publish` lays out.
    home = Path(tempfile.mkdtemp(prefix="factory-draft-"))
    root = write(home, it)
    check("D5 it satisfies the skill contract", complete(root), root.name)
    #: `write` will happily lay out a body that does not parse; the kernel would then bind
    #: a placeholder that raises only when called.
    try:
        compile(it.body, "<drafted>", "exec")
        valid, why = True, "the drafted body is valid Python"
    except SyntaxError as exc:
        valid, why = False, f"SyntaxError: {exc}"
    check("D5 and the body compiles", valid, why)

    # D6 -- an empty workflow is refused rather than published as a tool that does nothing.
    empty = True
    try:
        draft(Workflow(name="nothing"), a_run(held=True))
    except NotDrafted:
        empty = False
    credulous += empty
    check("D6 a workflow with no steps is refused", not empty, "NotDrafted")

    print(f"\nINVENTED  literals from nowhere in the record : {invented}   (must be 0)")
    print(f"CREDULOUS drafted from a run that did not work : {credulous}   (must be 0)")
    print(f"FAILED    cases not matching                   : {failed}")
    return 1 if invented or credulous or failed else 0


if __name__ == "__main__":
    sys.exit(run())
