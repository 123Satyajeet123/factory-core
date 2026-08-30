"""Executes vendors.toml, which claims to be the only place a revision is written down.

THE CLAIM IS WORTH NOTHING UNCHECKED. A manifest nothing verifies drifts silently: a clone
moves, an npm range takes a minor, and the number in the file stops describing the tree
while still reading as if it does. This makes the claim falsifiable.

THREE ECOSYSTEMS, ONE MANIFEST, AND `path` SAYS WHICH. A clone under `candidates/` is
pinned by commit and checked against `HEAD`; something under `node_modules/` is pinned by
version and read from its `package.json`; an empty path is a distribution, pinned by version
and read from installed metadata. The `use` field exists because an import is not the only
way to depend on a project, and a check that inspected only imports would see none of them.

MEASURED, ON THE FIRST RUN: `openadapt-flow` was declared as a clone at a commit and is
actually a PyPI distribution at 1.34.0, imported by `compile/`. The pinned revision was not
what ran, and nothing said so until this file existed.
"""

from __future__ import annotations

import json
import subprocess
import tomllib
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
MANIFEST = HERE / "vendors.toml"


@dataclass(frozen=True)
class State:
    """One vendor, as declared and as found."""

    name: str
    tier: int
    use: str
    want: str
    got: str
    where: Path

    @property
    def present(self) -> bool:
        return bool(self.got)

    @property
    def pinned(self) -> bool:
        #: A git rev is declared in full and reported in full; an npm version is declared
        #: with a leading `v` that the package itself does not carry.
        return self.present and self.got.startswith(self.want.lstrip("v")[:12])


def _git_head(path: Path) -> str:
    done = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"],
                          capture_output=True, text=True)
    return done.stdout.strip() if not done.returncode else ""


def _npm_version(path: Path) -> str:
    manifest = path / "package.json"
    if not manifest.exists():
        return ""
    return str(json.loads(manifest.read_text()).get("version", ""))


def _installed(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return ""


def declared() -> list[dict]:
    return tomllib.loads(MANIFEST.read_text())["vendor"]


def state() -> list[State]:
    """Every declared vendor, with what is actually on disk beside what was written down."""
    found = []
    for vendor in declared():
        where = HERE / vendor["path"] if vendor["path"] else HERE
        if not vendor["path"]:
            got = _installed(vendor["name"])
        elif "node_modules" in vendor["path"]:
            got = _npm_version(where)
        else:
            got = _git_head(where)
        found.append(State(name=vendor["name"], tier=vendor["tier"], use=vendor["use"],
                           want=vendor["rev"], got=got, where=where))
    return found


def sync() -> int:
    """Report every vendor against its pin. Non-zero when the tree stopped matching.

    Deliberately does not fetch or check out. A revision moving under a working tree is a
    decision, and a command that quietly made it would be the second mechanism this file
    exists to prevent.
    """
    drift = 0
    for vendor in state():
        if not vendor.present:
            mark, detail = "MISSING", "not installed" if vendor.where == HERE else \
                f"nothing at {vendor.where.relative_to(HERE)}"
        elif not vendor.pinned:
            mark, detail = "DRIFTED", f"declared {vendor.want}, found {vendor.got[:12]}"
        else:
            mark, detail = "ok", f"{vendor.got[:12]}"
        drift += mark != "ok"
        print(f"  {mark:8} {vendor.name:16} tier {vendor.tier}  use={vendor.use:14} {detail}")
    print(f"\n{len(state())} vendors declared, {drift} not matching the manifest (must be 0)")
    return 1 if drift else 0
