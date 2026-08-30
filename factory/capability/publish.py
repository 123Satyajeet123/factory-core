
from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel

from factory.core.errors import CapabilityFailed

FREE = ("requests", "httpx", "pyyaml", "tomli", "python-dotenv", "pandas", "numpy",
        "scipy", "beautifulsoup4", "lxml", "pydantic", "tyro")


def slug(name: str) -> str:
    return re.sub(r"[^0-9a-zA-Z]+", "-", name.strip()).strip("-").lower()


def importable(name: str) -> str:
    got = slug(name).replace("-", "_")
    if not got.isidentifier():
        raise CapabilityFailed(f"{name!r} does not map to a Python identifier")
    return got


class Capability(BaseModel):

    name: str
    description: str
    body: str
    needs: tuple[str, ...] = ()

    @property
    def module(self) -> str:
        return importable(self.name)

    def undeclared(self) -> tuple[str, ...]:
        return tuple(need for need in self.needs if need not in FREE)


SKILL_MD = """---
name: {name}
description: {description}
---


Call it from the kernel:

    await {module}(...)
"""

PYPROJECT = """[project]
name = "{name}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [{dependencies}]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/{module}"]
"""


def write(into: Path, capability: Capability) -> Path:
    root = into / capability.name
    package = root / "src" / capability.module
    package.mkdir(parents=True, exist_ok=True)

    deps = ", ".join(f'"{need}"' for need in capability.needs if need not in FREE)
    (root / "SKILL.md").write_text(SKILL_MD.format(
        name=capability.name, description=capability.description, module=capability.module))
    (root / "pyproject.toml").write_text(PYPROJECT.format(
        name=capability.name, module=capability.module, dependencies=deps))
    (package / "__init__.py").write_text(capability.body)
    return root


def complete(root: Path) -> bool:
    name = root.name.replace("-", "_")
    return all((root / part).exists() for part in
               ("SKILL.md", "pyproject.toml", Path("src") / name / "__init__.py"))
