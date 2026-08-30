from __future__ import annotations

import os

SECRET = "FACTORY_SECRET_"


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def model_key() -> str:
    return env("OPENROUTER_API_KEY")


def model_base() -> str:
    return env("FACTORY_MODEL_BASE")


def model_names() -> list[str]:
    return [n for n in env("FACTORY_MODELS").split(",") if n]


def secret(name: str) -> str | None:
    return env(f"{SECRET}{name.upper().replace('-', '_')}") or None
