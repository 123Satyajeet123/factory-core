"""What makes a run stop, and can a run raise its own ceiling?

    uv run python -m evals.run.stop_eval

gates/when-to-stop.md. No browser: every condition here is arithmetic over a run's own
evidence, and the property under test is that the reasons are distinguishable -- a run that
says only "stopped" is one nobody can act on.
"""

from __future__ import annotations

import sys

from factory.core.contract import Receipt, Verdict
from factory.core.evidence import Did, RowRun, Run, StepRun
from factory.core.question import Ask, Question
from factory.run import stop


def row(verdict: Verdict | None = None, *, irreversible: bool = False,
        refused: bool = False) -> RowRun:
    if refused:
        return RowRun(row={}, refused=Question(kind=Ask.PARAM, about="x", because="nobody"))
    return RowRun(row={}, steps=[StepRun(
        intent="a step", did=Did(ok=True), irreversible=irreversible,
        receipt=None if verdict is None else Receipt(verdict=verdict))])


def main() -> int:
    faults = 0
    cap = stop.Cap(rows=3, learning_nothing=2)

    def check(name: str, ok: bool, detail: str) -> None:
        nonlocal faults
        faults += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name:44} {detail}")

    #: C1. A cap is code's, and nothing may raise it -- including this eval.
    try:
        cap.rows = 999
        raised = True
    except Exception:
        raised = False
    check("C1 a cap cannot be raised from outside", not raised,
          "frozen" if not raised else "IT WAS RAISED")

    #: C3. Enough is not failure, and it is not the same as running out.
    met = stop.after_row(Run(rows=[row(Verdict.CONFIRMED)]), cap=cap,
                         goal=stop.Goal(confirmed=1))
    check("C3 enough is its own ending", met.because is stop.Because.ENOUGH and met.wanted,
          f"{met.because} (wanted={met.wanted})")

    out = stop.ran_out(Run(rows=[row(Verdict.CONFIRMED)]), cap=cap)
    check("C3 and so is running out", out.wanted and out.because is stop.Because.ROWS_RAN_OUT,
          f"{out.because}")

    #: C4. Irreversible and refuted stops now, ahead of every other condition.
    hurt = stop.after_row(Run(rows=[row(Verdict.REFUTED, irreversible=True)]), cap=cap)
    check("C4 an irreversible act that did not land stops it",
          hurt.because is stop.Because.REFUTED and not hurt.wanted, f"{hurt.because}")

    #: And a REVERSIBLE refutation does not: that is an ordinary bad row.
    fine = stop.after_row(Run(rows=[row(Verdict.REFUTED)]), cap=cap)
    check("C4 a reversible one does not", fine is None,
          "carried on" if fine is None else f"stopped: {fine.because}")

    #: C5. Rows that produce no receipt at all are a run learning nothing.
    quiet = stop.after_row(Run(rows=[row(), row()]), cap=cap)
    check("C5 grinding is a stop", quiet.because is stop.Because.GRINDING, quiet.detail)

    #: And a row that FAILED while teaching something is progress, not grinding.
    taught = stop.after_row(Run(rows=[row(Verdict.REFUTED), row(Verdict.REFUTED)]), cap=cap)
    check("C5 a failing row that taught something is not",
          taught is None, "carried on" if taught is None else f"stopped: {taught.because}")

    #: C2 and C6.
    capped = stop.after_row(Run(rows=[row(Verdict.CONFIRMED)] * 3), cap=cap)
    check("C2 a ceiling is its own reason",
          capped.because is stop.Because.CAPPED and not capped.wanted, capped.detail)
    check("C6 room left is reported when it was not reached", out.room_left == 2,
          f"{out.room_left} of {cap.rows} unused")

    print(f"\nFAULTS  {faults}   (must be 0)")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(main())
