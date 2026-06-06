# DGX Environment Report

Generated: 2026-06-06

## Scope

This report records the pre-training environment inspection for GridFlex Compute. No model training was run, no private coordination-kernel logic was inspected or modified, and the scheduler API contract was left unchanged.

## Repository Structure

Repository root inspected: `gridflex-compute`

Key folders present:

- `apps/api/app/main.py`
- `apps/dgx_pipeline/README.md`
- `apps/dgx_pipeline/notebooks/`
- `apps/dgx_pipeline/outputs/`
- `apps/dgx_pipeline/src/`
- `apps/ui/src/components/DashboardSpec.md`
- `data/raw/`
- `data/source/`
- `data/derived/`
- `data/processed/`
- `data/mock/`
- `docs/`
- `infra/`
- `packages/contracts/`

## Dataset Availability

Raw LCL smart-meter dataset found:

- `data/raw/LCLstdorToU.txt`

Header verified from the raw file:

```text
LCLid	stdorToU	DateTime	KWH/hh (per half hour)
```

Additional data assets present:

- `data/raw/Tariffs.xlsx`
- `data/raw/domain-dataset0.json`
- `data/source/data_profile.json`
- `data/source/lcl_30min_aggregate_preview.csv`
- `data/derived/grid_stress_profile_from_lcl.csv`
- `data/mock/gridflex_demo_response.json`

The existing data profile reports:

- Rows: `1048575`
- Unique households: `31`
- Date range: `2011-12-06 13:00:00` to `2014-02-28 00:00:00`
- Bad kWh rows: `31`
- Duplicate rows: `722`
- Mean half-hour kWh: `0.22970738279738379`
- Max half-hour kWh: `6.5279999`

## Required Folder Setup

The following folders were confirmed or created:

- `data/raw`
- `data/processed`
- `apps/dgx_pipeline/src`
- `apps/dgx_pipeline/notebooks`
- `apps/dgx_pipeline/outputs`

## Local VS Code Machine Check

Shell: Windows PowerShell

`nvidia-smi` result:

```text
nvidia-smi: not recognized as the name of a cmdlet, function, script file, or operable program.
```

Python environment used by VS Code/Pylance:

- Executable: `c:\VS Workspaces\Ganicore-Team-Hackathon\.venv\Scripts\python.exe`
- Python: `3.14.0`
- Platform: `Windows-11-10.0.26200-SP0`

Local package availability:

| Package | Installed | Version / Notes |
| --- | --- | --- |
| `cudf` | No | Not available locally |
| `cuml` | No | Not available locally |
| `cupy` | No | Not available locally |
| `pandas` | No | Not available locally |
| `sklearn` | No | Not available locally |
| `xgboost` | No | Not available locally |
| `fastapi` | No | Not available locally |
| `prometheus_client` | No | Not available locally |

Local CUDA Python checks:

- `cupy`: unavailable because `cupy` is not installed
- `torch`: unavailable because `torch` is not installed
- `CUDA_VISIBLE_DEVICES`: not set

## DGX SSH Environment Check

Host checked over SSH: `nvidia@scan-12.local`

Remote hostname:

```text
scan-12
```

DGX OS/Python platform:

- Python executable: `/usr/bin/python3`
- Python version: `3.12.3`
- Platform: `Linux-6.17.0-1021-nvidia-aarch64-with-glibc2.39`

## DGX GPU Availability

`nvidia-smi` is available on the DGX host.

Observed GPU/driver state:

- NVIDIA-SMI: `580.159.03`
- Driver Version: `580.159.03`
- CUDA Version: `13.0`
- GPU: `NVIDIA GB10`
- GPU index: `0`
- Persistence mode: `On`
- Temperature: `40C`
- GPU utilization at check time: `1%`
- Compute mode: `Default`

Processes using GPU at check time were graphical desktop processes, including Xorg, GNOME Shell, Firefox, Nautilus, and related desktop utilities.

## DGX Python Package Availability

Checked with `/usr/bin/python3` on `scan-12`.

| Package | Installed | Version / Notes |
| --- | --- | --- |
| `cudf` | No | RAPIDS cuDF is not installed in system Python |
| `cuml` | No | RAPIDS cuML is not installed in system Python |
| `cupy` | No | CuPy is not installed in system Python |
| `pandas` | No | pandas is not installed in system Python |
| `sklearn` | No | scikit-learn is not installed in system Python |
| `xgboost` | No | XGBoost is not installed in system Python |
| `fastapi` | No | FastAPI is not installed in system Python |
| `prometheus_client` | No | prometheus-client is not installed in system Python |

DGX CUDA Python checks:

- `CUDA_VISIBLE_DEVICES`: not set
- `cupy`: unavailable because `cupy` is not installed
- `torch`: unavailable because `torch` is not installed

## Summary

Available now:

- DGX host is reachable over SSH.
- DGX has an NVIDIA GPU visible through `nvidia-smi`.
- NVIDIA driver and CUDA runtime are present at the system level.
- Raw LCL dataset exists at `data/raw/LCLstdorToU.txt` with the expected columns.
- Pipeline working folders exist.

Not available in the checked Python environments:

- RAPIDS stack: `cudf`, `cuml`
- CUDA Python array package: `cupy`
- CPU fallback stack: `pandas`, `sklearn`
- Optional model/API packages: `xgboost`, `fastapi`, `prometheus_client`

## Recommendation Before Training

Create an isolated Python environment on the DGX before training. Prefer RAPIDS/cuDF/cuML where compatible with the DGX platform, CUDA `13.0`, Python `3.12`, and `aarch64`. If RAPIDS packages are not available for this platform combination, install the CPU fallback stack first so the demo pipeline can still run with `pandas` and `scikit-learn`.

No model training has been started yet.