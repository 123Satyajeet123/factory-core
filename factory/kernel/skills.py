"""Putting a package into the kernel's interpreter, and making a running one see it.

WHAT THIS OWNS AND WHAT IT DOES NOT. The kernel owns its venv, so installing into it lives
here. It does not own the skill FORMAT -- that is prime-agent's, and `capability/publish.py`
writes to it -- so nothing here inspects a layout or knows what a SKILL.md is.

INSTALLED MEANS IMPORTABLE AFTER A CACHE REFRESH, NOT WRITTEN TO DISK. An editable install
adds a `sys.path` entry through a `.pth` file, and `site` reads those at interpreter
startup. A kernel that was already running does not see one, however successfully the
install reported. Measured: `uv pip install` returned 0 and the next cell raised
`ModuleNotFoundError`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from factory.kernel import venv

#: Run in a cell before importing something installed since the kernel started.
REFRESH = """
import importlib, site, sysconfig
site.addsitedir(sysconfig.get_paths()["purelib"])
importlib.invalidate_caches()
"""


class NotInstallable(RuntimeError):
    """Nothing bare crosses this driver's boundary."""


def install(root: Path) -> None:
    """Editable, so the source on disk stays the thing that runs."""
    done = subprocess.run(
        ["uv", "pip", "install", "--python", str(venv.interpreter()), "-e", str(root)],
        capture_output=True, text=True)
    if done.returncode:
        raise NotInstallable(f"install failed for {root.name}: {done.stderr.strip()[-300:]}")
