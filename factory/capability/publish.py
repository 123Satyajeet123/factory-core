"""Write a capability in the format the kernel already understands.

THE FORMAT IS THE VENDOR'S, TAKEN WHOLE. prime-agent
`skills/skill-creator/references/python-skills.md` states the detection contract and it is
reproduced rather than reinterpreted: `SKILL.md`, `pyproject.toml` at the root, and
`src/<import_name>/__init__.py`. All three or the skill silently degrades to markdown-only,
which is the failure this module exists to make impossible -- a capability that loaded as
prose looks installed and is not callable.

THE IMPORT NAME IS DERIVED, NOT CHOSEN. Hyphens become underscores and the result must be a
Python identifier; the hatchling `packages` entry must name the same directory, because the
project name and the package directory always differ for a hyphenated name.

WHAT IS OURS: only the writing. The procedure comes from `draft.py`, which reads it out of a
Run, and the name is the one thing a model is asked for.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

#: Present in the kernel venv already, so depending on one is free. From the vendor's
#: reference; anything else has to be declared and installed.
FREE = ("requests", "httpx", "pyyaml", "tomli", "python-dotenv", "pandas", "numpy",
        "scipy", "beautifulsoup4", "lxml", "pydantic", "tyro")


def importable(name: str) -> str:
    """The import name the kernel will expose, derived from the capability's name."""
    got = name.strip().replace("-", "_")
    if not got.isidentifier():
        raise ValueError(f"{name!r} does not map to a Python identifier")
    return got


class Capability(BaseModel):
    """One procedure, ready to be written out.

    `body` is the source of `run()` and nothing else -- imports included, since the kernel
    imports the module and copies `run`'s signature and docstring onto it. Those become the
    capability's API documentation and its CLI, so they are not decoration.
    """

    name: str
    description: str
    body: str
    needs: tuple[str, ...] = ()

    @property
    def module(self) -> str:
        return importable(self.name)

    def undeclared(self) -> tuple[str, ...]:
        """Dependencies that are neither free in the kernel venv nor declared."""
        return tuple(need for need in self.needs if need not in FREE)


SKILL_MD = """---
name: {name}
description: {description}
---

# {name}

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
    """Lay out the three files. Returns the skill root, which is what installs.

    `prime-agent-runtime` is never declared even though `run()` executes beside it: the
    vendor's reference says it is bundled rather than published, so declaring it breaks the
    install everywhere except the kernel venv.
    """
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
    """Every file the detection contract names. Anything less degrades silently."""
    name = root.name.replace("-", "_")
    return all((root / part).exists() for part in
               ("SKILL.md", "pyproject.toml", Path("src") / name / "__init__.py"))
