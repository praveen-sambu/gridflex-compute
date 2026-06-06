from __future__ import annotations

import logging
import os
import time
from typing import Any

LOGGER = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_MODEL = "nvidia/nemotron-3-ultra-550b-a55b"
DEFAULT_TIMEOUT_SECONDS = 20.0
MAX_TOKENS = 100
TEMPERATURE = 0.2
TOP_P = 0.8
SYSTEM_PROMPT = "You write concise one-sentence grid operations explanations."


def _nim_base_url() -> str:
    value = os.getenv("NIM_BASE_URL", "").strip()
    return value.rstrip("/") if value else DEFAULT_BASE_URL


def _nim_model() -> str:
    value = os.getenv("NIM_MODEL", "").strip()
    return value or DEFAULT_MODEL


def _nim_timeout_seconds() -> float:
    value = os.getenv("NIM_TIMEOUT_SECONDS", "").strip()
    try:
        timeout = float(value) if value else DEFAULT_TIMEOUT_SECONDS
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS
    return timeout if timeout > 0 else DEFAULT_TIMEOUT_SECONDS


def _nvidia_api_key() -> str | None:
    value = os.getenv("NVIDIA_API_KEY", "").strip()
    return value or None


def _openai_available() -> bool:
    try:
        from openai import OpenAI  # noqa: F401
    except Exception:
        return False
    return True


def _classify_provider_error(exc: Exception) -> str:
    error_name = type(exc).__name__.lower()
    error_message = str(exc).lower()
    error_text = f"{error_name} {error_message}"

    if "timeout" in error_text:
        return "timeout"
    if "auth" in error_text or "401" in error_text or "403" in error_text:
        return "auth_error"
    if "rate" in error_text and "limit" in error_text or "429" in error_text:
        return "rate_limit"
    if any(token in error_text for token in ("api", "status", "connection", "server", "500", "502", "503", "504")):
        return "api_error"
    return "unknown_error"


def _sanitize_decision_context(decision_context: dict[str, Any]) -> dict[str, Any]:
    allowed_keys = (
        "job_id",
        "decision",
        "reason_code",
        "grid_stress_before",
        "grid_stress_after",
        "delay_minutes",
        "deadline_protected",
        "carbon_signal",
        "workload_type",
    )
    sanitized: dict[str, Any] = {}
    for key in allowed_keys:
        if key not in decision_context:
            continue
        value = decision_context[key]
        if isinstance(value, (str, int, float, bool)) or value is None:
            sanitized[key] = value
        else:
            sanitized[key] = str(value)
    return sanitized


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_score(value: Any) -> str | None:
    score = _float_or_none(value)
    if score is None:
        return None
    return f"{score:.2f}"


def _fallback_operator_message(decision_context: dict[str, Any]) -> str:
    context = _sanitize_decision_context(decision_context)
    job_id = str(context.get("job_id") or "this workload")
    decision = str(context.get("decision") or "scheduled").strip().lower()
    reason_code = str(context.get("reason_code") or "grid conditions").replace("_", " ").lower()
    grid_before = _format_score(context.get("grid_stress_before"))
    grid_after = _format_score(context.get("grid_stress_after"))
    delay_value = _float_or_none(context.get("delay_minutes"))
    carbon_signal = str(context.get("carbon_signal") or "").strip().lower()
    deadline_protected = context.get("deadline_protected")

    if decision == "shifted":
        action = f"{job_id} was shifted"
    elif decision in {"admitted_now", "run_now", "admitted"}:
        action = f"{job_id} runs now"
    else:
        action = f"{job_id} was scheduled"

    details: list[str] = []
    if grid_before and grid_after:
        details.append(f"grid stress improves from {grid_before} to {grid_after}")
    elif grid_before:
        details.append(f"grid stress was {grid_before}")

    if carbon_signal:
        details.append(f"the carbon signal is {carbon_signal}")

    if delay_value is not None and delay_value > 0:
        delay_minutes = int(delay_value) if delay_value.is_integer() else delay_value
        details.append(f"the delay is {delay_minutes} minutes")

    if deadline_protected is True:
        details.append("the deadline stays protected")
    elif deadline_protected is False:
        details.append("deadline pressure still has to be managed")

    if not details:
        details.append(f"the decision follows the local GridFlex fallback for {reason_code}")

    return f"{action} because " + ", ".join(details[:-1]) + (", and " if len(details) > 1 else "") + details[-1] + "."


def _decision_summary(decision_context: dict[str, Any]) -> str:
    context = _sanitize_decision_context(decision_context)
    decision = str(context.get("decision") or "scheduled").replace("_", " ").lower()
    parts = [f"job {decision}"]

    grid_before = _format_score(context.get("grid_stress_before"))
    grid_after = _format_score(context.get("grid_stress_after"))
    if grid_before and grid_after:
        parts.append(f"from grid stress {grid_before} to {grid_after}")
    elif grid_before:
        parts.append(f"at grid stress {grid_before}")

    delay_value = _float_or_none(context.get("delay_minutes"))
    if delay_value is not None and delay_value > 0:
        delay_minutes = int(delay_value) if delay_value.is_integer() else delay_value
        parts.append(f"delay {delay_minutes} minutes")

    if context.get("deadline_protected") is True:
        parts.append("deadline protected")
    elif context.get("deadline_protected") is False:
        parts.append("deadline not protected")

    carbon_signal = str(context.get("carbon_signal") or "").strip().lower()
    if carbon_signal:
        parts.append(f"carbon signal {carbon_signal}")

    return ", ".join(parts)


def _user_prompt_for_decision(decision_context: dict[str, Any]) -> str:
    return f"Explain this decision in one sentence: {_decision_summary(decision_context)}."


def _normalize_operator_message(content: Any) -> str | None:
    if isinstance(content, str):
        text = " ".join(content.split())
        return text or None

    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if hasattr(item, "text"):
                text = getattr(item, "text")
                if isinstance(text, str) and text.strip():
                    text_parts.append(text.strip())
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    text_parts.append(text.strip())
        if text_parts:
            return " ".join(text_parts)

    return None


def _response_payload(
    *,
    source: str,
    model: str,
    operator_message: str,
    provider_latency_ms: int | None,
    fallback_reason: str | None,
) -> dict[str, Any]:
    return {
        "source": source,
        "model": model,
        "operator_message": operator_message,
        "provider_latency_ms": provider_latency_ms,
        "fallback_reason": fallback_reason,
    }


def _execute_nim_prompt(*, user_prompt: str) -> tuple[dict[str, Any], str | None]:
    status = get_nim_status()
    model = status["model"]
    fallback_message = "Live NVIDIA explanation unavailable; using GridFlex fallback explanation."
    if not status["nim_enabled"]:
        return (
            _response_payload(
                source="fallback",
                model=model,
                operator_message=fallback_message,
                provider_latency_ms=None,
                fallback_reason=None,
            ),
            None,
        )

    api_key = _nvidia_api_key()
    if api_key is None:
        return (
            _response_payload(
                source="fallback",
                model=model,
                operator_message=fallback_message,
                provider_latency_ms=None,
                fallback_reason=None,
            ),
            None,
        )

    try:
        from openai import OpenAI
    except Exception:
        LOGGER.warning("OpenAI package is unavailable; using local NIM fallback explanation.")
        return (
            _response_payload(
                source="fallback",
                model=model,
                operator_message=fallback_message,
                provider_latency_ms=None,
                fallback_reason=None,
            ),
            "ImportError",
        )

    client = OpenAI(
        base_url=status["base_url"],
        api_key=api_key,
        timeout=_nim_timeout_seconds(),
    )

    started_at = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            top_p=TOP_P,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
    except Exception as exc:
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        fallback_reason = _classify_provider_error(exc)
        LOGGER.warning(
            "Hosted NIM explanation request failed (%s); using local fallback explanation.",
            fallback_reason,
        )
        return (
            _response_payload(
                source="fallback",
                model=model,
                operator_message=fallback_message,
                provider_latency_ms=latency_ms,
                fallback_reason=fallback_reason,
            ),
            type(exc).__name__,
        )

    latency_ms = int((time.perf_counter() - started_at) * 1000)
    message = None
    if getattr(response, "choices", None):
        choice = response.choices[0]
        if getattr(choice, "message", None) is not None:
            message = getattr(choice.message, "content", None)

    operator_message = _normalize_operator_message(message)
    if operator_message is None:
        return (
            _response_payload(
                source="fallback",
                model=model,
                operator_message=fallback_message,
                provider_latency_ms=latency_ms,
                fallback_reason="api_error",
            ),
            "EmptyResponseError",
        )

    return (
        _response_payload(
            source="nvidia-nim",
            model=model,
            operator_message=operator_message,
            provider_latency_ms=latency_ms,
            fallback_reason=None,
        ),
        None,
    )


def get_nim_status() -> dict[str, Any]:
    api_key_available = _nvidia_api_key() is not None
    nim_enabled = api_key_available and _openai_available()
    return {
        "nim_enabled": nim_enabled,
        "api_key_available": api_key_available,
        "model": _nim_model(),
        "base_url": _nim_base_url(),
        "mode": "hosted-nim" if nim_enabled else "fallback",
    }


def explain_decision_with_nim(decision_context: dict[str, Any]) -> dict[str, Any]:
    fallback_message = _fallback_operator_message(decision_context)
    provider_result, _ = _execute_nim_prompt(user_prompt=_user_prompt_for_decision(decision_context))
    if provider_result["source"] == "nvidia-nim":
        return provider_result

    return _response_payload(
        source="fallback",
        model=provider_result["model"],
        operator_message=fallback_message,
        provider_latency_ms=provider_result["provider_latency_ms"],
        fallback_reason=provider_result["fallback_reason"],
    )


def probe_nim_provider(prompt: str) -> dict[str, Any]:
    result, error_class = _execute_nim_prompt(user_prompt=prompt)
    preview_text = result["operator_message"][:300]
    if result["source"] == "fallback" and error_class is not None:
        preview_text = error_class

    status = get_nim_status()
    return {
        "key_present": status["api_key_available"],
        "model": status["model"],
        "base_url": status["base_url"],
        "status": result["source"],
        "latency_ms": result["provider_latency_ms"],
        "fallback_reason": result["fallback_reason"],
        "preview": preview_text,
    }