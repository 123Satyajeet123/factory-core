from __future__ import annotations

from typing import Any

from factory.core.ledger import Act, Segment, Whose


def drove(acts: list[Act], task: str, after: list[Any] | None = None) -> Segment:
    return Segment(whose=Whose.FACTORY, intent=task, acts=acts, after=after or [])


def corrected(acts: list[Act], task: str, took_over_after: int) -> Segment:
    return Segment(whose=Whose.PERSON, intent=task, acts=acts,
                   took_over_after=took_over_after)


def admissible(segments: list[Segment]) -> list[Segment]:
    return [segment for segment in segments if segment.by_person()]


def _self_check() -> None:
    """uv run python -m factory.authority.wheel"""
    from factory.core.verbs import Doing
    from factory.core.workflow import Target

    acts = [Act(doing=Doing.PRESS, target=Target(role="button", name="Save"),
                surface="http://x")]

    ours = drove(acts, "outreach")
    theirs = corrected(acts, "outreach", took_over_after=2)
    assert not ours.by_person() and theirs.by_person()
    assert theirs.took_over_after == 2 and ours.took_over_after is None
    assert admissible([ours, theirs]) == [theirs]
    print("wheel: the same acts are a demonstration or a replay by who was driving, "
          "and only one of them is admissible")


if __name__ == "__main__":
    _self_check()
