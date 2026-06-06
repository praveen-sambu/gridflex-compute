from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response

from .coordination_kernel_client import schedule_with_coordination_kernel
from .live_carbon_signal import fetch_live_carbon_signal
from .nim_explainer import explain_decision_with_nim, get_nim_status

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
