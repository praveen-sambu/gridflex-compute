from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = ROOT / ".env"


def load_env_file() -> None:
    if not ENV_PATH.exists():
        return

    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        key, separator, value = line.partition("=")
        if not separator:
            continue

        env_key = key.strip()
        if not env_key or env_key in os.environ:
            continue

        os.environ[env_key] = value.strip()