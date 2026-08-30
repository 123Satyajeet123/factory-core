
from __future__ import annotations

import subprocess
from pathlib import Path

from factory.core.errors import KernelFailed
from factory.kernel import venv

REFRESH = """
import importlib, site, sysconfig
site.addsitedir(sysconfig.get_paths()["purelib"])
importlib.invalidate_caches()
"""


class NotInstallable(KernelFailed):
    pass


def install(root: Path) -> None:
    done = subprocess.run(
        ["uv", "pip", "install", "--python", str(venv.interpreter()), "-e", str(root)],
        capture_output=True, text=True)
    if done.returncode:
        raise NotInstallable(f"install failed for {root.name}: {done.stderr.strip()[-300:]}")
