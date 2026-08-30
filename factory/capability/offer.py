"""Installed means callable, not written to disk.

A CAPABILITY THAT LOADED AS PROSE LOOKS INSTALLED. prime-agent's detection contract degrades
a skill missing any of its three files to markdown-only, with a load warning, and binds the
name to a placeholder that raises only when called. So the check here is not "did the
install command succeed" -- it is "can a cell call it and get an answer".

IT IS `.run(...)`, NOT `name(...)`. The vendor's reference says the kernel "wraps the module
so the module itself is an async callable", but that wrapping lives in prime-agent's
TypeScript host; `rlm.skill` ships only `cli`/`run_cli`. Measured: a plain import gives
`TypeError: 'module' object is not callable`, and the documented equivalent works. The
caller passes arguments and never has to know which form exists.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from factory.capability.publish import complete
from factory.kernel.skills import NotInstallable


async def offer(kernel: Any, root: Path, arguments: str = "") -> str:
    """Install it, then prove it answers. `arguments` is what goes inside `run(...)`.

    The layout is checked here because `publish` owns the format; the install is the
    kernel's because it owns the interpreter.
    """
    if not complete(root):
        raise NotInstallable(
            f"{root.name} is missing part of the skill contract; the kernel would load it "
            f"as markdown and bind a placeholder that raises when called")
    await kernel.install(root)

    module = root.name.replace("-", "_")
    cell = await kernel.run(f"import {module}\nawait {module}.run({arguments})", timeout=60)
    if cell.status != "ok":
        raise NotInstallable(f"{root.name} installed but does not answer: "
                             f"{cell.ename}: {cell.evalue}")
    return cell.result or ""
