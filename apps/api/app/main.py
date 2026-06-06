from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response

from .env_loader import load_env_file

load_env_file()

from .coordination_kernel_client import get_coordination_kernel_status, schedule_with_coordination_kernel
from .gpu_pulse_demo import gpu_pulse_capabilities, run_gpu_pulse_demo
from .live_carbon_signal import fetch_live_carbon_signal
from .nim_explainer import explain_decision_with_nim, get_nim_status
from .voice_agent import (
    get_audio_file_path,
    handle_voice_agent_message,
    record_voice_agent_event,
    voice_agent_evidence,
    voice_agent_session,
    voice_agent_status,
)

try:
    from fastapi.middleware.cors import CORSMiddleware
except Exception:  # pragma: no cover - middleware availability depends on FastAPI install
    CORSMiddleware = None

app = FastAPI(title="GridFlex Compute v2 API")

ROOT = Path(__file__).resolve().parents[3]
MOCK = ROOT / "data" / "mock" / "gridflex_demo_response.json"
DGX = ROOT / "data" / "mock" / "gridflex_demo_response_dgx.json"

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

if CORSMiddleware is not None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _payload_has_required_shape(payload: dict[str, Any]) -> bool:
    required_keys = {"run_id", "kpis", "grid_windows", "workloads", "decisions"}
    if not required_keys.issubset(payload.keys()):
        return False
    return all(
        isinstance(payload.get(key), expected_type)
        for key, expected_type in {
            "kpis": dict,
            "grid_windows": list,
            "workloads": list,
            "decisions": list,
        }.items()
    )


def _try_load_payload(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = _load_json(path)
    except (OSError, json.JSONDecodeError):
        return None
    return payload if _payload_has_required_shape(payload) else None


def _load_required_payload(path: Path, label: str) -> dict[str, Any]:
    payload = _try_load_payload(path)
    if payload is None:
        raise HTTPException(status_code=404, detail=f"{label} payload is missing or invalid")
    return payload


def _active_payload() -> tuple[str, dict[str, Any], bool]:
    dgx_payload = _try_load_payload(DGX)
    if dgx_payload is not None:
        return "dgx", dgx_payload, True

    mock_payload = _try_load_payload(MOCK)
    if mock_payload is not None:
        return "mock", mock_payload, False

    raise HTTPException(status_code=503, detail="No valid demo payload is available")


def _coordination_kernel_payload() -> dict[str, Any]:
    _, payload, _ = _active_payload()
    schedule_result = schedule_with_coordination_kernel(
        grid_windows=payload["grid_windows"],
        workloads=payload["workloads"],
    )
    if schedule_result is None:
        fallback_payload = dict(payload)
        fallback_payload["coordination_kernel_status"] = "fallback"
        return fallback_payload

    merged_payload = dict(payload)
    merged_payload["kpis"] = schedule_result["kpis"]
    merged_payload["decisions"] = schedule_result["decisions"]
    return merged_payload


def _carbon_orchestration_seed_workloads() -> list[dict[str, Any]]:
    return [
        {
            "job_id": "carbon-job-001",
            "workload_type": "llm_finetune",
            "gpu_count": 8,
            "estimated_duration_minutes": 180,
            "estimated_energy_kwh": 62.0,
            "urgency_class": "urgent",
            "deadline_minutes": 90,
        },
        {
            "job_id": "carbon-job-002",
            "workload_type": "batch_inference",
            "gpu_count": 4,
            "estimated_duration_minutes": 90,
            "estimated_energy_kwh": 18.0,
            "urgency_class": "flexible",
            "deadline_minutes": 360,
        },
        {
            "job_id": "carbon-job-003",
            "workload_type": "rag_embedding",
            "gpu_count": 2,
            "estimated_duration_minutes": 45,
            "estimated_energy_kwh": 7.0,
            "urgency_class": "interactive",
            "deadline_minutes": 60,
        },
        {
            "job_id": "carbon-job-004",
            "workload_type": "model_eval",
            "gpu_count": 2,
            "estimated_duration_minutes": 50,
            "estimated_energy_kwh": 9.0,
            "urgency_class": "standard",
            "deadline_minutes": 120,
        },
        {
            "job_id": "carbon-job-005",
            "workload_type": "nightly_training",
            "gpu_count": 8,
            "estimated_duration_minutes": 240,
            "estimated_energy_kwh": 88.0,
            "urgency_class": "flexible",
            "deadline_minutes": 600,
        },
        {
            "job_id": "carbon-job-006",
            "workload_type": "batch_inference",
            "gpu_count": 6,
            "estimated_duration_minutes": 150,
            "estimated_energy_kwh": 28.0,
            "urgency_class": "flexible",
            "deadline_minutes": 480,
        },
        {
            "job_id": "carbon-job-007",
            "workload_type": "llm_finetune",
            "gpu_count": 4,
            "estimated_duration_minutes": 120,
            "estimated_energy_kwh": 34.0,
            "urgency_class": "standard",
            "deadline_minutes": 180,
        },
        {
            "job_id": "carbon-job-008",
            "workload_type": "model_eval",
            "gpu_count": 1,
            "estimated_duration_minutes": 30,
            "estimated_energy_kwh": 4.0,
            "urgency_class": "urgent",
            "deadline_minutes": 45,
        },
    ]


def _is_urgent_workload(workload: dict[str, Any]) -> bool:
    return workload["urgency_class"] in {"urgent", "interactive"} or workload["deadline_minutes"] <= 90


def _carbon_policy_decision(
    workload: dict[str, Any],
    *,
    live_carbon: dict[str, Any],
) -> tuple[str, str, str]:
    if live_carbon.get("status") != "ok" or live_carbon.get("current_intensity") is None:
        fallback_message = "Live carbon unavailable; use GridFlex forecast."
        return ("use_gridflex_forecast", fallback_message, fallback_message)

    intensity = float(live_carbon["current_intensity"])
    workload_type = workload["workload_type"].replace("_", " ")
    urgent = _is_urgent_workload(workload)

    if intensity <= 180:
        return (
            "run_now",
            f"Carbon intensity is {intensity:.0f} gCO2/kWh, so this {workload_type} workload can run now.",
            f"Run {workload['job_id']} now because live carbon intensity is low and the workload fits the current policy window.",
        )

    if intensity <= 300:
        if urgent:
            return (
                "run_now",
                f"Carbon intensity is {intensity:.0f} gCO2/kWh. This workload is urgent enough to run now.",
                f"Run {workload['job_id']} now because it is urgent or interactive, even though carbon intensity is moderate.",
            )

        return (
            "request_cleaner_window",
            f"Carbon intensity is {intensity:.0f} gCO2/kWh, so flexible GPU work should wait for a cleaner window.",
            f"Delay {workload['job_id']} and request a cleaner resource window because the job is flexible and the carbon signal is only moderate.",
        )

    if urgent:
        return (
            "run_now",
            f"Carbon intensity is {intensity:.0f} gCO2/kWh, but this urgent workload still runs now to protect delivery timing.",
            f"Run {workload['job_id']} now because it is urgent and cannot wait, despite a high live carbon signal.",
        )

    return (
        "request_cleaner_window",
        f"Carbon intensity is {intensity:.0f} gCO2/kWh, so flexible GPU work should be delayed.",
        f"Delay {workload['job_id']} and request a cleaner resource window because live carbon intensity is high and the workload is flexible.",
    )


def _build_carbon_orchestration_demo() -> dict[str, Any]:
    live_carbon = fetch_live_carbon_signal()
    workloads: list[dict[str, Any]] = []
    jobs_run_now = 0
    jobs_delayed = 0
    estimated_energy_shifted_kwh = 0.0
    estimated_carbon_avoided_kgco2 = 0.0

    current_intensity = live_carbon.get("current_intensity")
    cleaner_window_target = 180.0

    for seed_workload in _carbon_orchestration_seed_workloads():
        decision, reason, operator_message = _carbon_policy_decision(seed_workload, live_carbon=live_carbon)
        workload = dict(seed_workload)
        workload["decision"] = decision
        workload["reason"] = reason
        workload["operator_message"] = operator_message
        workloads.append(workload)

        if decision == "run_now":
            jobs_run_now += 1
        elif decision == "request_cleaner_window":
            jobs_delayed += 1
            estimated_energy_shifted_kwh += float(workload["estimated_energy_kwh"])
            if isinstance(current_intensity, (int, float)):
                estimated_carbon_avoided_kgco2 += float(workload["estimated_energy_kwh"]) * max(
                    float(current_intensity) - cleaner_window_target,
                    0.0,
                ) / 1000.0

    if live_carbon.get("status") == "ok" and isinstance(current_intensity, (int, float)):
        if current_intensity <= 180:
            operator_summary = (
                f"Live carbon is low at {current_intensity:.0f} gCO2/kWh. Run most AI training and inference jobs now."
            )
        elif current_intensity <= 300:
            operator_summary = (
                f"Live carbon is moderate at {current_intensity:.0f} gCO2/kWh. Run urgent jobs now and hold flexible jobs for a cleaner window."
            )
        else:
            operator_summary = (
                f"Live carbon is high at {current_intensity:.0f} gCO2/kWh. Only urgent jobs should run now; flexible jobs should wait."
            )
    else:
        operator_summary = "Live carbon unavailable; use GridFlex forecast."

    return {
        "status": live_carbon.get("status", "fallback"),
        "source": "NESO Carbon Intensity API + GridFlex policy",
        "live_carbon": live_carbon,
        "kpis": {
            "jobs_total": len(workloads),
            "jobs_run_now": jobs_run_now,
            "jobs_delayed": jobs_delayed,
            "estimated_energy_shifted_kwh": round(estimated_energy_shifted_kwh, 1),
            "estimated_carbon_avoided_kgco2": round(estimated_carbon_avoided_kgco2, 3),
        },
        "workloads": workloads,
        "operator_summary": operator_summary,
    }


def _select_control_loop_job(payload: dict[str, Any]) -> dict[str, Any]:
    workloads = payload.get("workloads")
    if isinstance(workloads, list):
        for workload in workloads:
            if not isinstance(workload, dict):
                continue
            workload_type = str(workload.get("workload_type") or "").lower()
            if any(token in workload_type for token in ("finetune", "training")):
                return dict(workload)

    return {
        "job_id": "control-loop-job-001",
        "tenant": "ai-factory",
        "workload_type": "llm_finetune",
        "submitted_at": "2026-06-06T12:00:00Z",
        "duration_minutes": 120,
        "gpu_count": 8,
        "estimated_energy_kwh": 42.0,
        "urgency_class": "batch-flexible",
        "deadline_at": "2026-06-06T18:00:00Z",
    }


def _control_decision_from_signal(
    job: dict[str, Any],
    live_carbon: dict[str, Any],
    local_decision: dict[str, Any] | None,
    coordination_used: bool,
) -> tuple[str, str, float, float]:
    estimated_energy_kwh = _safe_float(job.get("estimated_energy_kwh"))
    recommendation = str(live_carbon.get("recommendation") or "use_gridflex_forecast")
    carbon_value = live_carbon.get("current_intensity")
    carbon_text = f"{float(carbon_value):.0f} gCO2/kWh" if isinstance(carbon_value, (int, float)) else "fallback forecast"
    delay_minutes = _safe_float(local_decision.get("delay_minutes")) if isinstance(local_decision, dict) else 0.0

    if recommendation == "run_now":
        reason = f"Live carbon is low at {carbon_text}, so the incoming training job can run now."
        if coordination_used and delay_minutes > 0:
            return (
                "run_selective",
                reason[:-1] + " while the coordination API keeps some flexible steps movable.",
                round(estimated_energy_kwh * 0.35, 2),
                delay_minutes,
            )
        return ("run_now", reason, 0.0, 0.0)

    if recommendation == "run_selective":
        reason = f"Live carbon is moderate at {carbon_text}, so only urgent setup and checkpoint work should run now."
        return ("run_selective", reason, round(estimated_energy_kwh * 0.4, 2), max(delay_minutes, 30.0))

    reason = f"Live carbon is elevated at {carbon_text}, so flexible DGX training should wait for a cleaner window."
    return ("delay", reason, round(estimated_energy_kwh, 2), max(delay_minutes, 60.0))


def _build_control_loop_demo() -> dict[str, Any]:
    active_name, payload, dgx_available = _active_payload()
    live_carbon = fetch_live_carbon_signal()
    coordination_status = get_coordination_kernel_status()
    nim_status = get_nim_status()
    sample_job = _select_control_loop_job(payload)
    local_decision = next(
        (
            decision
            for decision in payload.get("decisions", [])
            if isinstance(decision, dict) and decision.get("job_id") == sample_job.get("job_id")
        ),
        None,
    )

    coordination_result = schedule_with_coordination_kernel(
        grid_windows=payload.get("grid_windows", []),
        workloads=[sample_job],
    )
    coordination_used = coordination_result is not None
    coordination_decision = None
    if isinstance(coordination_result, dict):
        decisions = coordination_result.get("decisions")
        if isinstance(decisions, list) and decisions and isinstance(decisions[0], dict):
            coordination_decision = decisions[0]

    decision, reason, estimated_energy_shifted, delay_minutes = _control_decision_from_signal(
        sample_job,
        live_carbon,
        coordination_decision or local_decision,
        coordination_used,
    )

    chosen_decision = coordination_decision or local_decision or {}
    current_window = payload.get("grid_windows", [None])[0] if isinstance(payload.get("grid_windows"), list) else None
    nim_response = explain_decision_with_nim(
        {
            "job_id": sample_job.get("job_id"),
            "decision": decision,
            "reason_code": chosen_decision.get("reason_code") or "LIVE_CARBON_POLICY",
            "grid_stress_before": chosen_decision.get("grid_stress_before") or (current_window or {}).get("predicted_grid_stress_score") or (current_window or {}).get("grid_stress_score"),
            "grid_stress_after": chosen_decision.get("grid_stress_after") or chosen_decision.get("grid_stress_before") or (current_window or {}).get("predicted_grid_stress_score") or (current_window or {}).get("grid_stress_score"),
            "delay_minutes": delay_minutes,
            "deadline_protected": True,
            "carbon_signal": live_carbon.get("index") or live_carbon.get("recommendation"),
            "workload_type": sample_job.get("workload_type"),
        }
    )

    return {
        "status": "ok",
        "active_payload": active_name,
        "live_carbon_signal": live_carbon,
        "sample_incoming_ai_training_job": sample_job,
        "decision": decision,
        "reason": reason,
        "estimated_energy_shifted_kwh": estimated_energy_shifted,
        "operator_message": nim_response["operator_message"],
        "source_fields": {
            "live_carbon_used": live_carbon.get("status") == "ok",
            "coordination_api_used": coordination_used,
            "coordination_api_fallback": not coordination_used,
            "nemotron_used": nim_response.get("source") == "nvidia-nim",
            "nemotron_fallback": nim_response.get("source") != "nvidia-nim",
            "dgx_payload_used": dgx_available,
        },
        "sources": {
            "live_carbon_used": live_carbon.get("status") == "ok",
            "coordination_api_used": coordination_used,
            "coordination_api_fallback": not coordination_used,
            "nemotron_used": nim_response.get("source") == "nvidia-nim",
            "nemotron_fallback": nim_response.get("source") != "nvidia-nim",
            "dgx_payload_used": dgx_available,
        },
        "component_sources": {
            "live_carbon": live_carbon.get("source"),
            "coordination_api": coordination_status["mode"],
            "nemotron": nim_response.get("source"),
            "dgx_payload": "dgx" if dgx_available else active_name,
            "gpu_pulse": gpu_pulse_capabilities(),
        },
        "readiness": _demo_readiness(),
    }


def _demo_readiness() -> dict[str, Any]:
    active_name, _, dgx_available = _active_payload()
    live_carbon = fetch_live_carbon_signal()
    coordination_status = get_coordination_kernel_status()
    nim_status = get_nim_status()
    pulse_status = gpu_pulse_capabilities()
    return {
        "dgx_backend_ready": pulse_status["nvidia_smi_available"] or pulse_status["nvcc_available"],
        "demo_payload_ready": active_name in {"dgx", "mock"},
        "live_carbon_ready": live_carbon.get("status") == "ok",
        "coordination_api_ready_public": coordination_status["configured"],
        "nim_configured": nim_status["nim_enabled"],
        "gpu_pulse_enabled": pulse_status["gpu_pulse_enabled"],
        "metrics_ready": True,
        "dgx_payload_used": dgx_available,
    }


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _build_metrics_text(payload: dict[str, Any], dgx_available: bool) -> str:
    kpis = payload.get("kpis", {})
    jobs_total = max(1.0, _safe_float(kpis.get("jobs_total")))
    jobs_shifted = _safe_float(kpis.get("jobs_shifted"))
    metrics = [
        ("gridflex_jobs_total", "Total demo jobs in the active payload.", _safe_float(kpis.get("jobs_total"))),
        ("gridflex_jobs_shifted_total", "Jobs shifted to lower-stress windows.", jobs_shifted),
        ("gridflex_jobs_admitted_now_total", "Jobs admitted immediately.", _safe_float(kpis.get("jobs_admitted_now"))),
        ("gridflex_peak_kwh_avoided", "Estimated peak kWh avoided.", _safe_float(kpis.get("peak_kwh_avoided"))),
        (
            "gridflex_gpu_utilisation_preserved_pct",
            "Estimated GPU utilisation preserved percentage.",
            _safe_float(kpis.get("gpu_utilisation_preserved_pct")),
        ),
        (
            "gridflex_grid_stress_before",
            "Mean grid stress before scheduling decisions.",
            _safe_float(kpis.get("mean_grid_stress_before")),
        ),
        (
            "gridflex_grid_stress_after",
            "Mean grid stress after scheduling decisions.",
            _safe_float(kpis.get("mean_grid_stress_after")),
        ),
        (
            "gridflex_deadline_miss_rate",
            "Deadline miss rate for the active demo payload.",
            _safe_float(kpis.get("deadline_miss_rate")),
        ),
        (
            "gridflex_estimated_carbon_saving_kgco2",
            "Estimated carbon saving in kgCO2.",
            _safe_float(kpis.get("estimated_carbon_saving_kgco2")),
        ),
        ("gridflex_payload_available", "Whether any active payload is available.", 1.0),
        ("gridflex_dgx_payload_available", "Whether a valid DGX payload is available.", 1.0 if dgx_available else 0.0),
        (
            "gridflex_decision_shift_ratio",
            "Ratio of shifted jobs to total jobs.",
            jobs_shifted / jobs_total,
        ),
    ]

    lines: list[str] = []
    for name, help_text, value in metrics:
        lines.append(f"# HELP {name} {help_text}")
        lines.append(f"# TYPE {name} gauge")
        lines.append(f"{name} {value}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"

@app.get("/health")
def health():
    active_name, _, dgx_available = _active_payload()
    return {
        "status": "ok",
        "service": "gridflex-api",
        "active_payload": active_name,
        "dgx_payload_available": dgx_available,
    }

@app.get("/api/v1/demo")
def demo():
    _, payload, _ = _active_payload()
    return payload


@app.get("/api/v1/control-loop-demo")
def control_loop_demo():
    return _build_control_loop_demo()


@app.post("/api/v1/gpu-pulse-demo")
def gpu_pulse_demo():
    return run_gpu_pulse_demo()


@app.get("/api/v1/demo-readiness")
def demo_readiness():
    return _demo_readiness()


@app.get("/api/v1/demo-coord")
def demo_coord():
    return _coordination_kernel_payload()


@app.get("/api/v1/live-carbon")
def live_carbon():
    return fetch_live_carbon_signal()


@app.get("/api/v1/carbon-orchestration-demo")
def carbon_orchestration_demo():
    return _build_carbon_orchestration_demo()


@app.get("/api/v1/nim-status")
def nim_status():
    return get_nim_status()


@app.post("/api/v1/explain-decision")
def explain_decision(decision_context: dict[str, Any]):
    return explain_decision_with_nim(decision_context)


@app.get("/api/v1/voice-agent/status")
def get_voice_agent_status():
    return voice_agent_status()


@app.get("/api/v1/voice-agent/session")
def get_voice_agent_session():
    return voice_agent_session(limit=200)


@app.get("/api/v1/voice-agent/evidence")
def get_voice_agent_evidence():
    return voice_agent_evidence()


@app.post("/api/v1/voice-agent/event")
def post_voice_agent_event(payload: dict[str, Any]):
    event_type = str(payload.get("event_type") or "").strip()
    message = str(payload.get("message") or "").strip()
    if not event_type or not message:
        raise HTTPException(status_code=400, detail="event_type and message are required")

    extra = {
        str(key): value
        for key, value in payload.items()
        if key not in {"event_type", "message"}
    }
    return record_voice_agent_event(event_type, message, extra=extra)


@app.post("/api/v1/voice-agent/message")
def post_voice_agent_message(payload: dict[str, Any]):
    message = str(payload.get("message") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")
    return handle_voice_agent_message(message)


@app.get("/api/v1/voice-agent/audio/{filename}")
def get_voice_agent_audio(filename: str):
    audio_file = get_audio_file_path(filename)
    if audio_file is None:
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(audio_file, media_type="audio/mpeg", filename=audio_file.name)


@app.get("/api/v1/demo-dgx")
def demo_dgx():
    return _load_required_payload(DGX, "DGX demo")


@app.get("/api/v1/demo-original")
def demo_original():
    return _load_required_payload(MOCK, "Original demo")


@app.get("/api/v1/kpis")
def kpis():
    _, payload, _ = _active_payload()
    return payload["kpis"]


@app.get("/api/v1/decisions")
def decisions():
    _, payload, _ = _active_payload()
    return payload["decisions"]


@app.get("/api/v1/grid-windows")
def grid_windows():
    _, payload, _ = _active_payload()
    return payload["grid_windows"]

@app.get("/metrics")
def metrics():
    _, payload, dgx_available = _active_payload()
    return Response(
        _build_metrics_text(payload, dgx_available),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
