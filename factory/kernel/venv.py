
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from factory.core.errors import KernelFailed

HERE = Path(__file__).resolve().parents[2]
VENV = HERE / ".venv-kernel"
RUNTIME = HERE / "candidates" / "prime-agent" / "prime-agent-runtime"

KEEP = ("PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "TERM")


def interpreter() -> Path:
    return VENV / ("Scripts" if sys.platform == "win32" else "bin") / "python"


def environment() -> dict[str, str]:
    kept = {name: os.environ[name] for name in KEEP if name in os.environ}
    return kept | {"PYTHONPATH": "", "PYTHONNOUSERSITE": "1"}


def ready() -> bool:
    return interpreter().exists()


def build() -> Path:
    if not RUNTIME.exists():
        raise KernelFailed(f"prime-agent is not cloned; expected {RUNTIME}")
    if not ready():
        subprocess.run(["uv", "venv", str(VENV)], check=True, capture_output=True)
    subprocess.run(
        ["uv", "pip", "install", "--python", str(interpreter()), "-e", str(RUNTIME)],
        check=True, capture_output=True)
    return interpreter()
