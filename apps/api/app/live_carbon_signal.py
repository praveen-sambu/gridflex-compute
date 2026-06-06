from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

NESO_CARBON_INTENSITY_URL = "https://api.carbonintensity.org.uk/intensity"
TIMEOUT_SECONDS = 5
FALLBACK_REASON = "Live carbon signal unavailable; using GridFlex DGX-trained forecast instead."


def _fallback_response() -> dict[str, Any]:
    return {
        "status": "fallback",
        "source": "fallback",
        "current_intensity": None,
        "index": "unknown",
        "recommendation": "use_gridflex_forecast",
        "reason": FALLBACK_REASON,
        "operator_message": "Live carbon signal unavailable; using GridFlex forecast. Keep flexible jobs movable and follow the GridFlex schedule guidance.",
    }


def _guidance_for_intensity(current_intensity: float) -> tuple[str, str, str]:
    if current_intensity <= 180:
        return (
            "run_now",
            "Live carbon intensity is low, so running GPU jobs now is carbon-efficient.",
            "Carbon intensity is low right now. Run time-sensitive and standard GPU jobs now.",
        )

    if current_intensity <= 300:
        return (
            "run_selective",
            "Live carbon intensity is moderate, so urgent jobs can run now while flexible jobs remain schedulable.",
            "Carbon intensity is moderate. Run urgent workloads now and keep flexible jobs available for lower-carbon windows.",
        )

    return (
        "delay_flexible_jobs",
        "Live carbon intensity is high, so flexible jobs should be delayed if deadlines allow.",
        "Carbon intensity is high. Delay flexible GPU jobs and prefer the next lower-carbon GridFlex window.",
    )


def fetch_live_carbon_signal() -> dict[str, Any]:
    request = urllib.request.Request(
        NESO_CARBON_INTENSITY_URL,
        headers={"Accept": "application/json"},
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            response_body = response.read().decode("utf-8")
    except (urllib.error.HTTPError, urllib.error.URLError, OSError):
        return _fallback_response()

    try:
        parsed = json.loads(response_body)
    except json.JSONDecodeError:
        return _fallback_response()

    entries = parsed.get("data")
    if not isinstance(entries, list) or not entries or not isinstance(entries[0], dict):
        return _fallback_response()

    entry = entries[0]
    intensity_data = entry.get("intensity")
    if not isinstance(intensity_data, dict):
        return _fallback_response()

    actual = intensity_data.get("actual")
    forecast = intensity_data.get("forecast")
    current_value = actual if isinstance(actual, (int, float)) else forecast if isinstance(forecast, (int, float)) else None
    if current_value is None:
        return _fallback_response()

    recommendation, reason, operator_message = _guidance_for_intensity(float(current_value))
    index = intensity_data.get("index") if isinstance(intensity_data.get("index"), str) else "unknown"

    return {
        "status": "ok",
        "source": "NESO Carbon Intensity API",
        "current_intensity": float(current_value),
        "index": index,
        "from": entry.get("from"),
        "to": entry.get("to"),
        "recommendation": recommendation,
        "reason": reason,
        "operator_message": operator_message,
    }