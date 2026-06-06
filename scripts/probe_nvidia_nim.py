from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.nim_explainer import probe_nim_provider  # noqa: E402


def _load_dotenv_if_present() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator:
            continue
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = value.strip()


def main() -> int:
    _load_dotenv_if_present()
    prompt = "Explain this decision in one sentence: job shifted from grid stress 0.72 to 0.41, delay 120 minutes, deadline protected, carbon signal low."
    result = probe_nim_provider(prompt)

    print(f"key_present={str(result['key_present']).lower()}")
    print(f"model={result['model']}")
    print(f"base_url={result['base_url']}")
    print(f"status={result['status']}")
    print(f"latency_ms={result['latency_ms']}")
    print(f"fallback_reason={result['fallback_reason']}")
    print(f"preview={result['preview'][:300]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())