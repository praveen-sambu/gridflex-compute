from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response

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
    "http://127.0.0.1:3000",
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
