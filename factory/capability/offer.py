
from __future__ import annotations

from pathlib import Path
from typing import Any

from factory.capability.publish import complete
from factory.kernel.skills import NotInstallable


async def offer(kernel: Any, root: Path, arguments: str = "") -> str:
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
