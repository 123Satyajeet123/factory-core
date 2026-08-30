"""The kernel's own interpreter, and why it is not ours.

TWO REASONS, AND ONLY ONE OF THEM IS ARITHMETIC. `prime-agent-runtime` requires
`mcp>=2,<3`; this tree runs `mcp` 1.26 under `browser/serve.py` and `door_eval`. That
conflict is real today and would evaporate on a version bump, so it is not what this rests
on -- see gates/kernel-isolation.md.

THE REASON THAT DOES NOT EXPIRE: a cell is model-written code. Sharing an interpreter means
sharing our imports, our open database handle and our environment, and the environment is
where the keys are. `environment()` below is the whole of K1 and it is deliberately an
allowlist: a scrub that names what to remove goes stale the first time a new key is added.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
VENV = HERE / ".venv-kernel"
RUNTIME = HERE / "candidates" / "prime-agent" / "prime-agent-runtime"

#: Everything a Python process needs to start and nothing that identifies us. PATH is
#: included because the runtime shells out for `rlm.bash`; it carries no secret.
KEEP = ("PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "TERM")


def interpreter() -> Path:
    return VENV / ("Scripts" if sys.platform == "win32" else "bin") / "python"


def environment() -> dict[str, str]:
    """An allowlist, never a denylist. A cell inherits nothing it was not handed."""
    kept = {name: os.environ[name] for name in KEEP if name in os.environ}
    #: The runtime is installed into the kernel venv, so nothing of ours is importable.
    #: Setting this empty also stops the parent's cwd leaking onto the child's path.
    return kept | {"PYTHONPATH": "", "PYTHONNOUSERSITE": "1"}


def ready() -> bool:
    return interpreter().exists()


def build() -> Path:
    """Create the interpreter and install the runtime into it. Idempotent.

    Editable, so the pinned checkout in `candidates/` is what runs -- a copy would be a
    second revision nobody wrote down.
    """
    if not RUNTIME.exists():
        raise RuntimeError(f"prime-agent is not cloned; expected {RUNTIME}")
    if not ready():
        subprocess.run(["uv", "venv", str(VENV)], check=True, capture_output=True)
    subprocess.run(
        ["uv", "pip", "install", "--python", str(interpreter()), "-e", str(RUNTIME)],
        check=True, capture_output=True)
    return interpreter()
