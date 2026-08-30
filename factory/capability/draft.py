
from __future__ import annotations

from factory.capability.publish import Capability, importable, slug
from factory.core.errors import CapabilityFailed
from factory.core.evidence import Run
from factory.core.verbs import Doing
from factory.core.workflow import Step, Workflow


class NotDrafted(CapabilityFailed):
    pass


def _literal(text: str) -> str:
    return repr(text)


def _act(step: Step, params: tuple[str, ...]) -> list[str]:
    if step.doing is Doing.GO:
        where = step.param if step.param in params else _literal(step.value)
        return [f'if not await act("go", url={where}): return done']

    if step.target is None:
        raise NotDrafted(f"the {step.doing} step has no target, so it cannot be replayed")
    role, name = _literal(step.target.role), _literal(step.target.name)

    if step.doing is Doing.PRESS:
        return [f'if not await act("click", role={role}, name={name}): return done']

    written = step.param if step.param in params else _literal(step.value)
    return [f'if not await act("click", role={role}, name={name}): return done',
            f'if not await act("write", text={written}): return done']


def worked(run: Run) -> bool:
    return any(row.ran and row.steps and all(s.did.ok for s in row.steps)
               for row in run.rows)


def draft(workflow: Workflow, run: Run, *, name: str | None = None) -> Capability:
    if not workflow.steps:
        raise NotDrafted(f"{workflow.name} has no steps")
    if not worked(run):
        raise NotDrafted(
            f"no row of this run completed {workflow.name}; there is nothing to publish")

    called = slug(name or workflow.name)
    importable(called)
    signature = ", ".join(f"{param}: str" for param in workflow.params)
    lines = [line for step in workflow.steps for line in _act(step, workflow.params)]
    intents = [step.intent for step in workflow.steps if step.intent]

    body = "\n".join([
        '"""Drafted from a run, not written. See capability/draft.py."""',
        "",
        "import rlm.mcp as mcp",
        "",
        "",
        f"async def run({signature}) -> list[dict]:",
        f'    """{called}: {", ".join(intents) or f"{len(workflow.steps)} steps"}.',
        "",
        "    Every act goes through the BROWSER door, so each one is guarded and witnessed.",
        "    Returns what each act reported, and stops at the first that did not hold.",
        '    """',
        "    done: list[dict] = []",
        "",
        "    async def act(tool: str, **args: str) -> bool:",
        '        got = await mcp.call_tool("browser", tool, args)',
        "        done.append(got)",
        '        return bool(got.get("ok"))',
        "",
        *(f"    {line}" for line in lines),
        "    return done",
        "",
    ])
    return Capability(name=called, description=_describe(workflow), body=body)


def _describe(workflow: Workflow) -> str:
    takes = f" Takes {', '.join(workflow.params)}." if workflow.params else ""
    return (f"{len(workflow.steps)} steps, drafted from a run that completed.{takes}")
