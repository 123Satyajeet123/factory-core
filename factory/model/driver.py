
from __future__ import annotations

import asyncio
import json
import time
import urllib.error
import urllib.request
from typing import Any

from pydantic import BaseModel, ValidationError

from factory import settings


class Refused(BaseModel):

    why: str
    model: str = ""
    said: str = ""

    def __bool__(self) -> bool:
        return False


class Answered(BaseModel):

    value: Any
    model: str
    seconds: float = 0.0
    tokens: int = 0

    def __bool__(self) -> bool:
        return True


def _post(url: str, key: str, body: dict[str, Any], seconds: float) -> dict[str, Any]:
    request = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=seconds) as got:
        return json.load(got)


async def ask[Wanted: BaseModel](
        situation: str, wanted: type[Wanted], *, models: list[str], key: str,
        base_url: str, seconds: float = 60.0) -> Answered | Refused:
    schema = wanted.model_json_schema()
    schema["additionalProperties"] = False
    last = Refused(why="no models were offered")

    for model in models:
        started = time.perf_counter()
        body = {
            "model": model,
            "messages": [{"role": "user", "content": situation}],
            "response_format": {"type": "json_schema", "json_schema": {
                "name": wanted.__name__.lower(), "strict": True, "schema": schema}},
        }
        try:
            answer = await asyncio.to_thread(
                _post, f"{base_url}/chat/completions", key, body, seconds)
        except Exception as unreachable:
            last = Refused(why=f"{type(unreachable).__name__}: {unreachable}"[:200],
                           model=model)
            continue

        said = (answer.get("choices") or [{}])[0].get("message", {}).get("content") or ""
        try:
            value = wanted.model_validate_json(said)
        except ValidationError as malformed:
            last = Refused(why=f"did not conform: {malformed.error_count()} problems",
                           model=model, said=said[:200])
            continue

        used = (answer.get("usage") or {}).get("total_tokens") or 0
        return Answered(value=value, model=model, tokens=int(used),
                        seconds=time.perf_counter() - started)
    return last


MODELS = [
    "nvidia/nemotron-3.5-lightning:free",
    "minimax/minimax-m3:free",
]


def configured() -> tuple[str, str, list[str]] | None:
    key, where = settings.model_key(), settings.model_base()
    if not key or not where:
        return None
    return key, where, settings.model_names() or MODELS


def chooser(models: list[str] | None = None) -> Any:
    settings_now = configured()
    if settings_now is None:
        return None
    key, where, offered = settings_now

    from factory.model.schemas_resolve import Chosen, situation

    async def choose(wanted: str, among: dict[int, str]) -> int | None:
        got = await ask(situation(wanted, among), Chosen,
                        models=models or offered, key=key, base_url=where)
        return got.value.picked() if got else None

    return choose


def _self_check() -> None:
    import os

    for name in ("OPENROUTER_API_KEY", "FACTORY_MODEL_BASE"):
        os.environ.pop(name, None)
    assert configured() is None, "no key and no endpoint is not a configured driver"
    assert chooser() is None, "absent is a state, never a stub that guesses"

    os.environ["OPENROUTER_API_KEY"] = "not-a-real-key"
    assert configured() is None, "a key without an endpoint is still not configured"
    os.environ["FACTORY_MODEL_BASE"] = "http://127.0.0.1:1"
    key, where, offered = configured()
    assert (key, where) == ("not-a-real-key", "http://127.0.0.1:1"), "read from settings"
    assert offered == MODELS, "the shipped list when none is named"

    os.environ["FACTORY_MODELS"] = "one:free,two:free"
    assert configured()[2] == ["one:free", "two:free"], "named models win"

    refused = asyncio.run(ask("anything", Answered, models=[], key="k", base_url="x"))
    assert not refused and refused.why, "no models offered is a refusal, not a crash"

    unreachable = asyncio.run(
        ask("anything", Answered, models=["m"], key="k",
            base_url="http://127.0.0.1:1", seconds=1.0))
    assert not unreachable and unreachable.model == "m", "unreachable is a refusal too"
    print("model: absent without configuration, and a refusal is a value")


if __name__ == "__main__":
    _self_check()
