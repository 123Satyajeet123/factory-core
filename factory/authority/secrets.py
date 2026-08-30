from __future__ import annotations

import re

from factory import settings

MARK = "secret:"
NAMED = re.compile(rf"{MARK}([A-Za-z0-9_.-]+)")


def reference(name: str) -> str:
    return f"{MARK}{name}"


def held(value: str | None) -> bool:
    return bool(value) and value.startswith(MARK)


def name_of(value: str) -> str:
    return value[len(MARK):]


def reveal(value: str) -> str | None:
    if not held(value):
        return value
    return settings.secret(name_of(value))


def redact(text: str) -> str:
    return NAMED.sub(f"{MARK}\\1", text)


def leaked(text: str) -> list[str]:
    return [name for name in {n for n in NAMED.findall(text)}
            if (secret := reveal(reference(name))) and secret in text]
