"""The MODEL driver: a situation and a schema in, that schema or a typed refusal out.

A REFUSAL IS A VALUE, NOT AN EXCEPTION. `gates/model-vendor.md` D2: a caller branches on
"it would not answer" without catching anything, and a best-effort object with empty fields
is worse than either -- that is the shape that makes `locate` press the wrong control.

NO SILENT RETRY. Conformance is measured on the FIRST response, because a library whose
correctness comes from retrying pays for it in tokens and calls it reliability. Retrying is
a decision a caller makes with the refusal in hand.

NO CLIENT LIBRARY, AND THAT IS THIS GATE'S OWN RULE. D6 asks whether a second provider costs
a config line or a code path; a plain OpenAI-compatible POST costs a base url either way.
The gate's decision rule says a dependency that only smooths an API we call once is not
adopted, and `response_format: json_schema` is that API. What a client would add here is
retries we do not want and provider branching we do not have.

FREE IS AN OBSERVATION. Which models cost nothing comes from a provider's own listing --
`catalogue` asks -- never from a price table, whose failing case is on record.
"""

from __future__ import annotations

import asyncio
import json
import time
import urllib.error
import urllib.request
from typing import Any

from pydantic import BaseModel, ValidationError


class Refused(BaseModel):
    """The model would not, or could not, answer in the shape asked for."""

    why: str
    model: str = ""
    #: What it said instead, when it said anything. A refusal nobody can read is
    #: indistinguishable from a crash.
    said: str = ""

    def __bool__(self) -> bool:
        return False


class Answered(BaseModel):
    """One answer, and what it cost to get."""

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
    """Ask the first model that answers in the shape. No retries within a model."""
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
            #: THE ANSWER CAME BACK AND IS NOT THE SHAPE. That is a refusal, not an error:
            #: the caller wanted a decision and did not get one, and which of the two it
            #: was does not change what they can do about it.
            last = Refused(why=f"did not conform: {malformed.error_count()} problems",
                           model=model, said=said[:200])
            continue

        used = (answer.get("usage") or {}).get("total_tokens") or 0
        return Answered(value=value, model=model, tokens=int(used),
                        seconds=time.perf_counter() - started)
    return last
