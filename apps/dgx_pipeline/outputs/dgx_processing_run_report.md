# DGX Processing Run Report

Generated: 2026-06-06

## Run Target

- Hostname: `scan-12`
- Repo path on DGX: `~/gridflex-compute`
- Raw input: `~/gridflex-compute/data/raw/LCLstdorToU.txt`

## DGX System Evidence

- Python executable: `/home/nvidia/gridflex-compute/.venv-dgx/bin/python`
- Python version: `3.12.3 (main, Mar 23 2026, 19:04:32) [GCC 13.3.0]`
- Platform: `Linux-6.17.0-1021-nvidia-aarch64-with-glibc2.39`

`nvidia-smi` summary captured during run:

```text
NVIDIA GB10, 580.159.03, 37, 0 %
```

## Environment Used On DGX

- Virtual environment: `.venv-dgx`
- Reliable CPU/demo stack installed: `pandas`, `scikit-learn`, `fastapi`, `uvicorn`, `prometheus-client`, `numpy`, `joblib`
- CuPy installed: `cupy-cuda13x==14.1.1`
- RAPIDS attempt: started, but not completed in the allotted time; `cudf` was still unavailable at runtime

## GPU / RAPIDS Evidence

CuPy GPU test result:

```text
python 3.12.3 (main, Mar 23 2026, 19:04:32) [GCC 13.3.0]
platform Linux-6.17.0-1021-nvidia-aarch64-with-glibc2.39
cupy 14.1.1
cupy_sum 49999995994112.0
GPU_TEST=PASS
```

Runtime package visibility during the DGX pipeline run:

- `pandas`: installed, version `3.0.3`
- `cupy`: installed, version `14.1.1`
- `sklearn`: installed, version `1.9.0`
- `fastapi`: installed, version `0.136.3`
- `prometheus_client`: installed
- `cudf`: not installed / not importable at runtime

## Backend Used By The Pipeline

- `pandas` used: `Yes`
- `cuDF` used: `No`
- CuPy GPU test passed: `Yes`

The DGX pipeline log showed:

```text
[gridflex-lcl] cuDF unavailable; falling back to pandas (ModuleNotFoundError: No module named 'cudf').
[gridflex-lcl] Using processing backend: pandas
```

## Exact Command Used

```bash
python apps/dgx_pipeline/src/process_lcl_data.py --input data/raw/LCLstdorToU.txt --output-dir data/processed
```

This command was executed on the DGX after activating the environment:

```bash
cd ~/gridflex-compute
. .venv-dgx/bin/activate
python apps/dgx_pipeline/src/process_lcl_data.py --input data/raw/LCLstdorToU.txt --output-dir data/processed
```

## Processing Summary

- Row count before cleaning: `1,048,575`
- Row count after cleaning: `1,048,544`
- Row count after duplicate removal: `1,047,822`
- Number of 30-minute windows: `39,095`
- Unique households: `31`
- Date range: `2011-12-06T13:00:00` to `2014-02-28T00:00:00`

Stress distribution:

- Low: `76.33%`
- Medium: `22.53%`
- High: `1.13%`

## File Outputs Generated On DGX

- `~/gridflex-compute/data/processed/grid_stress_30min.csv`
- `~/gridflex-compute/data/processed/grid_stress_features.csv`
- `~/gridflex-compute/apps/dgx_pipeline/outputs/data_profile.json`
- `~/gridflex-compute/apps/dgx_pipeline/outputs/data_processing_report.md`

## Outcome

The DGX processing run succeeded.

GPU availability was confirmed through `nvidia-smi`, and CUDA-backed execution was confirmed through a passing CuPy test. However, the actual LCL processing pipeline used `pandas` on DGX because `cudf` was not available in the DGX environment at runtime. No model training was started.