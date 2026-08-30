"""Does anything bare cross a driver boundary?

    uv run python -m evals.bare

`core/errors.py` says nothing bare crosses one. It said so with no mechanism, and nine
`RuntimeError`s and `ValueError`s crossed one anyway while three drivers each hand-rolled
their own class. A caller could not tell "no browser is installed" from "ghost-cursor is
missing" from a genuine bug without matching on the message.

`main.py` is exempt and that is the whole exemption: it is the composition root, nothing is
above it, and an error there crosses no boundary because there is no other side.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRIVERS = ROOT / "factory"

BARE = {"RuntimeError", "ValueError", "TypeError", "KeyError", "OSError", "Exception"}
EXEMPT = {"factory/main.py", "factory/core/errors.py"}


def raised(path: Path) -> list[tuple[int, str]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return []
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Raise) or node.exc is None:
            continue
        call = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
        name = getattr(call, "id", None) or getattr(call, "attr", None)
        if name in BARE:
            found.append((node.lineno, name))
    return found


def main() -> int:
    offences = 0
    scanned = 0
    for path in sorted(DRIVERS.rglob("*.py")):
        here = str(path.relative_to(ROOT))
        if here in EXEMPT:
            continue
        scanned += 1
        for line, name in raised(path):
            offences += 1
            print(f"{here}:{line}  raises a bare {name}")

    print(f"\n{scanned} driver files scanned, {offences} raising something bare "
          f"(must be 0)")
    return 1 if offences else 0


def _self_check() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as home:
        good = Path(home) / "typed.py"
        good.write_text("from x import KernelFailed\ndef f():\n    raise KernelFailed('no')\n")
        assert raised(good) == [], raised(good)

        bad = Path(home) / "loose.py"
        bad.write_text("def f():\n    raise RuntimeError('no')\n")
        assert raised(bad) == [(2, "RuntimeError")], raised(bad)


if __name__ == "__main__":
    _self_check()
    sys.exit(main())
