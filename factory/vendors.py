
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


if __name__ == "__main__":
    raise SystemExit(sync())
