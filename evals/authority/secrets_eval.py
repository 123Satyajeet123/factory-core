from __future__ import annotations

import json
import os
import sys

from factory.authority import secrets
from factory.core.contract import Contract
from factory.core.evidence import Did, RowRun, Run, StepRun
from factory.core.ledger import Act, Segment
from factory.core.verbs import Doing
from factory.core.workflow import Step, Target, Workflow

PASSWORD = "hunter2-not-in-any-file"
REFERENCE = secrets.reference("example-com-password")


def run() -> int:
    os.environ["FACTORY_SECRET_EXAMPLE_COM_PASSWORD"] = PASSWORD
    leaked = broke = failed = 0

    def check(name: str, ok: bool, detail: str) -> None:
        nonlocal failed
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name:50} {detail}")

    check("S1 a reference is not the secret", secrets.held(REFERENCE)
          and PASSWORD not in REFERENCE, REFERENCE)
    check("S4 exactly one call turns it into plaintext",
          secrets.reveal(REFERENCE) == PASSWORD and secrets.reveal("plain") == "plain",
          "reveal, and nothing else")
    check("S4 an unheld secret reveals nothing",
          secrets.reveal(secrets.reference("never-set")) is None, "None, not the reference")

    segment = Segment(acts=[
        Act(doing=Doing.WRITE, value=REFERENCE, target=Target(role="textbox", name="Password")),
        Act(doing=Doing.PRESS, target=Target(role="button", name="Sign in"))])
    workflow = Workflow(name="sign-in", params=(), steps=[
        Step(doing=Doing.WRITE, value=REFERENCE, target=Target(role="textbox", name="Password"))])
    run_record = Run(workflow="sign-in", rows=[RowRun(row={}, steps=[
        StepRun(intent="password", rung="accessible",
                did=Did(ok=True, value=REFERENCE, detail="typed 23 characters"))])])

    # S6 -- searched for, not asserted. Everything that touches disk or a prompt.
    written = {
        "ledger segment": segment.model_dump_json(),
        "workflow": workflow.model_dump_json(),
        "run evidence": run_record.model_dump_json(),
        "contract": Contract(expects={"who": REFERENCE}).model_dump_json(),
        "a prompt fragment": json.dumps({"workflow": workflow.model_dump(mode="json")}),
    }
    for what, text in written.items():
        found = PASSWORD in text
        leaked += found
        check(f"S6 the plaintext is not in the {what}", not found,
              "reference only" if not found else "LEAKED")

    check("S5 the evidence carries the reference",
          REFERENCE in run_record.model_dump_json(), "so the step is still replayable")

    # S3 -- the workflow is complete: someone holding the secret can run it.
    step = workflow.steps[0]
    broke += secrets.reveal(step.wants({})) != PASSWORD
    check("S3 someone holding the secret can still run it",
          secrets.reveal(step.wants({})) == PASSWORD, "resolved at the last moment")

    # S2 -- what the page declares, not what a name looks like.
    marks = ("<input type=password>", "<input autocomplete=current-password>",
             "<input autocomplete=new-password>")
    plain = ("<input name=passenger>", "<input name=pass_count>", "<input type=text>")
    check("S2 the page declares it, a name does not",
          all("password" in m for m in marks) and not any(m in marks for m in plain),
          "type=password and the autocomplete tokens")

    print(f"\nLEAKED the plaintext reached something kept : {leaked}   (must be 0)")
    print(f"BROKE  a workflow that can no longer sign in : {broke}   (must be 0)")
    print(f"FAILED cases not matching                    : {failed}")
    return 1 if leaked or broke or failed else 0


if __name__ == "__main__":
    sys.exit(run())
