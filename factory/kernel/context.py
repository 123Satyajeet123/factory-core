"""Hand a model a handle, never the object.

RLM IS A CONTEXT MECHANISM. prime-agent name it Recursive Language Models: keep the large
object in the REPL as a variable and let the model query it by writing code, rather than
loading it into a prompt. A ledger, a run trace, a DOM serialisation of 201 elements and a
body of exchanges are all things this system has, and none of them should enter a context
window whole.

WHAT THE VENDOR SUPPLIES AND WHAT IT DOES NOT. `rlm` supplies the persistent namespace and
the code execution -- that is the whole mechanism and it is adopted, not rebuilt. It ships
no helper for the other half: getting an object in without it passing through a prompt, and
describing it well enough that a model can write a useful first query. `rlm.harness` is a
registry of skills and `overview()` renders that registry, not an arbitrary object;
prime-agent's own "admission handle" is a child-agent spawn result. Searched, none found,
so the two functions below are ours and they are the measured gap.

REJECTED: uploading the object to the provider and querying it in a hosted sandbox. It
works and it is somebody else's machine. This system's evidence is a person's own browser
traffic and their own ledger; sending it out to be able to ask about it inverts the premise.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from factory.kernel import venv

#: Under the kernel's own venv, which is git-ignored. A handle is a working file, never a
#: record -- the ledger is the record.
HANDLES = venv.VENV / "handles"

#: How much of the object is worth showing. Enough to write a first query against, and not
#: enough to be the object.
PREVIEW = 400


class Handle(BaseModel):
    """What a model is told about an object it cannot see.

    `saved` and `shown` are both bytes, and the ratio between them is the only claim this
    module makes: it is what the object would have cost in a prompt against what it did.
    """

    name: str
    kind: str
    rows: int | None = None
    fields: list[str] = []
    saved: int = 0
    shown: int = 0

    def prompt(self) -> str:
        """The fragment that enters a context window. Everything else stays in the kernel."""
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
    """Put an object in the kernel's namespace and return what a model may be told.

    THE OBJECT GOES BY FILE, NOT BY CELL. Inlining it as source would push every byte
    through the protocol and into the runtime's linecache, which is the prompt problem
    moved one process to the left rather than solved.
    """
    if not name.isidentifier():
        raise ValueError(f"{name!r} is not a Python name")
    HANDLES.mkdir(parents=True, exist_ok=True)
    body = json.dumps(value)
    path = HANDLES / f"{name}.json"
    path.write_text(body, encoding="utf-8")

    cell = await kernel.run(
        f"import json, pathlib\n"
        f"{name} = json.loads(pathlib.Path({str(path)!r}).read_text())\n"
        f"len({name}) if hasattr({name}, '__len__') else 1")
    if cell.status != "ok":
        raise RuntimeError(f"could not place {name}: {cell.ename}: {cell.evalue}")
    return _describe(name, value, body)
