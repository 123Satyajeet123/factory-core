"""Which checks does this change actually touch?

    uv run python -m evals.which                 # against the working tree
    uv run python -m evals.which factory/browser/guard.py

Running everything after every edit is how a suite becomes something people skip. This
answers the smaller question -- what could this change possibly have broken -- by reading
the import graph rather than a table somebody has to keep true.

IMPORTS ARE READ, NOT GUESSED. A hand-written map of file to suite is a second thing to
maintain and the first thing to rot. This parses the tree, so a module that stops being
imported stops being covered, and that shows up here rather than in a passing run that
proved nothing.

DEFERRED IMPORTS COUNT. Half this tree imports inside functions to keep a driver's vendor
out of the import path, so a scan that only read the top of a file would miss most edges.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _module(path: Path) -> str:
    return ".".join(path.relative_to(ROOT).with_suffix("").parts)


def imports(path: Path) -> set[str]:
    """Every in-tree module this file imports, wherever the import is written."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return set()
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
            found |= {f"{node.module}.{alias.name}" for alias in node.names}
        elif isinstance(node, ast.Import):
            found |= {alias.name for alias in node.names}
    return {name for name in found if name.startswith(("factory", "evals"))}


def graph() -> dict[str, set[str]]:
    return {_module(p): imports(p)
            for p in [*ROOT.glob("factory/**/*.py"), *ROOT.glob("evals/**/*.py")]}


def reaches(edges: dict[str, set[str]], start: str) -> set[str]:
    """Everything `start` depends on, however deep."""
    seen, todo = set(), [start]
    while todo:
        at = todo.pop()
        for used in edges.get(at, set()):
            if used not in seen:
                seen.add(used)
                todo.append(used)
    return seen


def suites() -> list[str]:
    """Anything runnable: an eval, or a module carrying its own check."""
    found = []
    for path in sorted(ROOT.glob("evals/**/*_eval.py")):
        found.append(_module(path))
    for path in sorted(ROOT.glob("factory/**/*.py")):
        if "_self_check" in path.read_text(encoding="utf-8"):
            found.append(_module(path))
    return found


def touched(changed: list[str]) -> list[str]:
    edges = graph()
    names = {_module(ROOT / c) for c in changed if c.endswith(".py")}
    return [s for s in suites() if s in names or names & reaches(edges, s)]


def changed_now() -> list[str]:
    got = subprocess.run(["git", "diff", "--name-only", "HEAD"], cwd=ROOT,
                         capture_output=True, text=True, check=False)
    return [line for line in got.stdout.splitlines() if line.endswith(".py")]


def main() -> int:
    changed = sys.argv[1:] or changed_now()
    if not changed:
        print("nothing changed")
        return 0
    hits = touched(changed)
    print(f"changed: {', '.join(changed)}")
    print(f"touches {len(hits)} of {len(suites())} checks:")
    for name in hits:
        print(f"  uv run python -m {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
