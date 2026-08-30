"""Installed means callable, not written to disk.

A CAPABILITY THAT LOADED AS PROSE LOOKS INSTALLED. The vendor's contract degrades a skill
missing any of its three files to markdown-only, with a warning nobody reads, and the name
is then bound to a placeholder that raises only when called. So the check here is not "did
the install command succeed" -- it is "can a cell call it and get an answer".

EDITABLE, INTO THE KERNEL'S OWN VENV. `venv.build()` put the runtime there; a capability
goes beside it, so `uv pip install -e` is the whole mechanism and the source on disk stays
the thing that runs.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from factory.capability.publish import complete
from factory.kernel import venv


class NotInstallable(RuntimeError):
    """Nothing bare crosses this boundary."""


def install(root: Path) -> None:
    """Put the skill in the kernel venv. Refuses an incomplete layout rather than warn."""
    if not complete(root):
        raise NotInstallable(
            f"{root.name} is missing part of the skill contract; the kernel would load it "
            f"as markdown and bind a placeholder that raises when called")
    done = subprocess.run(
        ["uv", "pip", "install", "--python", str(venv.interpreter()), "-e", str(root)],
        capture_output=True, text=True)
    if done.returncode:
        raise NotInstallable(f"install failed for {root.name}: {done.stderr.strip()[-300:]}")


#: A running interpreter fixed `sys.path` at startup, and an editable install adds a new
#: entry via a `.pth` that only `site` reads. Importing is not enough; the path itself has
#: to be reprocessed. Measured: the first install here raised ModuleNotFoundError on a
#: kernel that `uv pip install` had just reported success for.
REFRESH = """
import importlib, site, sysconfig
site.addsitedir(sysconfig.get_paths()["purelib"])
importlib.invalidate_caches()
"""


async def offer(kernel: Any, root: Path, arguments: str = "") -> str:
    """Install it, then prove it answers. `arguments` is what goes inside `run(...)`.

    This is the whole of what "installed" means here: a name the kernel can import and an
    answer it can return. A successful install command is not that.

    IT IS `.run(...)`, NOT `name(...)`, AND THAT IS THE VENDOR'S DOING. The reference says
    the kernel "wraps the module so the module itself is an async callable" -- but that
    wrapping lives in prime-agent's TypeScript host, which loads skills. `rlm.skill` ships
    only `cli`/`run_cli`; there is no Python helper for it. Measured: a plain import gives a
    module and `await name(...)` raises `TypeError: 'module' object is not callable`. The
    documented equivalent `await name.run(...)` works, so the caller is spared knowing
    either -- it passes arguments and this builds the call.
    """
    install(root)
    module = root.name.replace("-", "_")
    cell = await kernel.run(
        f"{REFRESH}import {module}\nawait {module}.run({arguments})", timeout=60)
    if cell.status != "ok":
        raise NotInstallable(f"{root.name} installed but does not answer: "
                             f"{cell.ename}: {cell.evalue}")
    return cell.result or ""
