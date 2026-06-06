from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any

LOGGER = logging.getLogger(__name__)
TIMEOUT_SECONDS = 3


def _coordination_kernel_enabled() -> bool:
    return os.getenv("COORD_KERNEL_ENABLED", "false").strip().lower() == "true"


def _coordination_kernel_url() -> str | None:
    value = os.getenv("COORD_KERNEL_API_URL", "").strip()
    return value.rstrip("/") if value else None


def _coordination_kernel_key() -> str | None:
    value = os.getenv("COORD_KERNEL_API_KEY", "").strip()
    return value or None


def _extract_schedule_result(payload: Any) -> dict[str, Any] | None:
    candidates: list[Any] = [payload]
    if isinstance(payload, dict):
        candidates.extend(payload.get(key) for key in ("payload", "result", "data"))

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        kpis = candidate.get("kpis")
        decisions = candidate.get("decisions")
        if isinstance(kpis, dict) and isinstance(decisions, list):
            return {"kpis": kpis, "decisions": decisions}

    return None


def schedule_with_coordination_kernel(
    *,
    grid_windows: list[dict[str, Any]],
    workloads: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not _coordination_kernel_enabled():
        return None

    api_url = _coordination_kernel_url()
    api_key = _coordination_kernel_key()
    if not api_url or not api_key:
        LOGGER.warning(
            "Coordination kernel is enabled but URL or API key is missing; falling back to local demo payload."
        )
        return None

    body = json.dumps({"grid_windows": grid_windows, "workloads": workloads}).encode("utf-8")
    request = urllib.request.Request(
        f"{api_url}/v1/schedule",
        data=body,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-API-Key": api_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        LOGGER.warning(
            "Coordination kernel request failed with status %s; falling back to local demo payload.",
            exc.code,
        )
        return None
    except urllib.error.URLError as exc:
        LOGGER.warning(
            "Coordination kernel request could not be completed (%s); falling back to local demo payload.",
            exc.reason,
        )
        return None
    except OSError as exc:
        LOGGER.warning("Coordination kernel request failed (%s); falling back to local demo payload.", exc)
        return None

    try:
        parsed = json.loads(response_body)
    except json.JSONDecodeError:
        LOGGER.warning("Coordination kernel returned invalid JSON; falling back to local demo payload.")
        return None

    result = _extract_schedule_result(parsed)
    if result is None:
        LOGGER.warning(
            "Coordination kernel response did not include valid kpis and decisions; falling back to local demo payload."
        )
    return result