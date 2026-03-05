from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values

from vacancy_pipeline_py import paths


def load_env(path: Path | None = None) -> dict[str, str]:
    target = path or paths.env_file_path()
    if not target.exists():
        return {}
    values = dotenv_values(target)
    cleaned: dict[str, str] = {}
    for key, value in values.items():
        if not key or value is None:
            continue
        cleaned[key.lstrip("\ufeff")] = value
    return cleaned


def get_env(name: str, default: str = "", *, env_path: Path | None = None) -> str:
    value = os.getenv(name)
    if value is not None and value != "":
        return value
    return load_env(env_path).get(name, default)
