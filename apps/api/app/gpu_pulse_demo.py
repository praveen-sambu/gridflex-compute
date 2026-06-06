from __future__ import annotations

import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from typing import Any

SAFE_LIMIT_SECONDS = 5.0


def gpu_pulse_enabled() -> bool:
    return os.getenv("ENABLE_GPU_PULSE_DEMO", "false").strip().lower() == "true"


def _numpy_available() -> bool:
    try:
        import numpy  # noqa: F401
    except Exception:
        return False
    return True


def gpu_pulse_capabilities() -> dict[str, Any]:
    return {
        "gpu_pulse_enabled": gpu_pulse_enabled(),
        "nvidia_smi_available": shutil.which("nvidia-smi") is not None,
        "nvcc_available": shutil.which("nvcc") is not None,
        "numpy_available": _numpy_available(),
    }


def _nvidia_smi_snapshot() -> str | None:
    if shutil.which("nvidia-smi") is None:
        return None
    try:
        completed = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,utilization.gpu,temperature.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=2,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    output = completed.stdout.strip()
    return output or None


def _run_numpy_pulse(time_budget_seconds: float) -> tuple[str, dict[str, Any]]:
    import numpy as np

    target_seconds = max(0.25, min(1.5, time_budget_seconds - 0.5))
    generator = np.random.default_rng(42)
    left = generator.random((1024, 1024), dtype=np.float32)
    right = generator.random((1024, 1024), dtype=np.float32)
    iterations = 0
    checksum = 0.0
    started = time.perf_counter()

    while time.perf_counter() - started < target_seconds and iterations < 6:
        product = left @ right
        checksum = float(product[0, 0])
        iterations += 1

    return (
        "numpy",
        {
            "iterations": iterations,
            "checksum": round(checksum, 6),
            "target_runtime_seconds": round(target_seconds, 3),
        },
    )


def _run_fallback_pulse(time_budget_seconds: float) -> tuple[str, dict[str, Any]]:
    target_seconds = max(0.15, min(0.75, time_budget_seconds - 0.5))
    iterations = 0
    accumulator = 0
    started = time.perf_counter()

    while time.perf_counter() - started < target_seconds and iterations < 4:
        accumulator = sum(index * index for index in range(250_000))
        iterations += 1

    return (
        "fallback",
        {
            "iterations": iterations,
            "checksum": accumulator,
            "target_runtime_seconds": round(target_seconds, 3),
        },
    )


def run_gpu_pulse_demo() -> dict[str, Any]:
    if not gpu_pulse_enabled():
        return {"status": "disabled", "message": "GPU pulse disabled by environment"}

    started_at = datetime.now(timezone.utc).isoformat()
    nvidia_smi_before = _nvidia_smi_snapshot()
    started = time.perf_counter()

    if _numpy_available():
        backend_used, pulse_details = _run_numpy_pulse(SAFE_LIMIT_SECONDS)
    else:
        backend_used, pulse_details = _run_fallback_pulse(SAFE_LIMIT_SECONDS)

    duration_ms = int((time.perf_counter() - started) * 1000)
    nvidia_smi_after = _nvidia_smi_snapshot()

    return {
        "status": "ok",
        "started_at": started_at,
        "duration_ms": duration_ms,
        "backend_used": backend_used,
        "safe_limit_seconds": SAFE_LIMIT_SECONDS,
        "nvidia_smi_before": nvidia_smi_before,
        "nvidia_smi_after": nvidia_smi_after,
        "details": pulse_details,
    }