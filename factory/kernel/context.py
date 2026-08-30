
from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from factory.core.errors import KernelFailed
from factory.kernel import venv

HANDLES = venv.VENV / "handles"

PREVIEW = 400


class Handle(BaseModel):

    name: str
    kind: str
    rows: int | None = None
    fields: list[str] = []
    saved: int = 0
    shown: int = 0

    def prompt(self) -> str:
        shape = f"{self.rows} items" if self.rows is not None else self.kind
        fields = f", fields {', '.join(self.fields)}" if self.fields else ""
        return (f"`{self.name}` is a {self.kind} held in the kernel ({shape}{fields}). "
                f"It is not in this context. Query it by writing Python against `{self.name}`.")


def _describe(name: str, value: Any, body: str) -> Handle:
    rows = len(value) if isinstance(value, (list, dict)) else None
    fields: list[str] = []
    if isinstance(value, list) and value and isinstance(value[0], dict):
        fields = sorted(value[0])[:8]
    elif isinstance(value, dict):
        fields = sorted(value)[:8]
    handle = Handle(name=name, kind=type(value).__name__, rows=rows, fields=fields,
                    saved=len(body))
    handle.shown = len(handle.prompt())
    return handle


async def place(kernel: Any, name: str, value: Any) -> Handle:
    if not name.isidentifier():
        raise KernelFailed(f"{name!r} is not a Python name")
    HANDLES.mkdir(parents=True, exist_ok=True)
    body = json.dumps(value)
    path = HANDLES / f"{name}.json"
    path.write_text(body, encoding="utf-8")

    cell = await kernel.run(
        f"import json, pathlib\n"
        f"{name} = json.loads(pathlib.Path({str(path)!r}).read_text())\n"
        f"len({name}) if hasattr({name}, '__len__') else 1")
    if cell.status != "ok":
        raise KernelFailed(f"could not place {name}: {cell.ename}: {cell.evalue}")
    return _describe(name, value, body)
