"""Does any driver know a destination?

    uv run python -m evals.agnostic

The factory is supposed to build the things a workflow needs. A driver that names a site,
a selector or a procedure has quietly done that job by hand, and it will keep working on
the one destination somebody had in mind while silently being useless on the next.

This is mechanical rather than a matter of judgement, because the failure looks reasonable
every single time it happens.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

DRIVERS = Path(__file__).resolve().parents[1] / "factory"

#: A hostname that is not this host. Loopback is how a fixture is served.
HOST = re.compile(r"\bhttps?://(?!127\.0\.0\.1|localhost)[a-z0-9.-]+\.[a-z]{2,}", re.I)
#: A selector rooted at an id, or an xpath. Per-destination knowledge written in code.
#:
#: THIS PATTERN FIRED ON ITSELF THREE TIMES, and each round narrowed what it claims.
#: `".strip()` and `" ".join(...)` matched when a quote followed by a dot was enough.
#: `".venv-kernel"` matched when a lone `.name` was enough -- a dotfile and a class are the
#: same characters. `location.href`, `motion.js` and `rlm.repl` matched when `tag.class`
#: was enough -- so is every dotted identifier in Python.
#:
#: SO A CLASS SELECTOR IS NOT DETECTED, and that is stated rather than papered over. An
#: `#id` and an xpath are unambiguous; `.save-button` is indistinguishable from a filename
#: by regex, and a check that flags directory names is a check somebody switches off, which
#: catches nothing at all. The gap is real and this is where it is written down.
SELECTOR = re.compile(r"""(["'])\s*(?:\#[A-Za-z][\w-]*[\w .\#>:\[\]=-]*|//[a-z]+\[)\1""")

#: A name a person would recognise as a product rather than as a mechanism.
NAMED = re.compile(r"\b(apollo|gmail|sheets|linkedin|salesforce|hubspot|notion)\b", re.I)

#: Vendor URLs in a docstring are provenance, not knowledge. A line that only cites where
#: an idea came from is allowed to name a repository.
CITED = re.compile(r"github\.com|arxiv\.org|primeintellect|browser-use|playwright\.dev")


def offences(text: str, path: Path) -> list[tuple[int, str, str]]:
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        if CITED.search(line):
            continue
        for what, pattern in (("host", HOST), ("selector", SELECTOR), ("product", NAMED)):
            if pattern.search(line):
                found.append((number, what, line.strip()[:88]))
    return found


def main() -> int:
    bad = 0
    for path in sorted(DRIVERS.rglob("*.py")):
        for number, what, line in offences(path.read_text(encoding="utf-8"), path):
            bad += 1
            print(f"{path.relative_to(DRIVERS.parent)}:{number}  {what:9} {line}")
    scanned = sum(1 for _ in DRIVERS.rglob("*.py"))
    print(f"\n{scanned} driver files scanned, {bad} that know a destination (must be 0)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
