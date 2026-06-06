# Demo Response Generation Report

- hostname: `scan-12`
- exact Python executable: `/home/nvidia/gridflex-compute/.venv-dgx/bin/python`
- input files used:
  - `/home/nvidia/gridflex-compute/data/processed/grid_stress_predictions.csv`
  - `/home/nvidia/gridflex-compute/data/mock/gridflex_demo_response.json`
  - `/home/nvidia/gridflex-compute/packages/contracts/gridflex_response.schema.json`
- output files created:
  - `/home/nvidia/gridflex-compute/data/mock/gridflex_demo_response_dgx.json`
  - `/home/nvidia/gridflex-compute/apps/dgx_pipeline/outputs/demo_response_generation_report.md`
  - `/home/nvidia/gridflex-compute/apps/dgx_pipeline/outputs/demo_response_summary.json`
- number of grid windows: `36`
- number of workloads: `36`
- number of decisions: `36`
- number of shifted jobs: `15`
- KPI summary: `{'jobs_total': 36, 'jobs_shifted': 15, 'jobs_admitted_now': 21, 'deadline_miss_rate': 0, 'gpu_utilisation_preserved_pct': 97.08, 'peak_kwh_avoided': 3.5173, 'mean_grid_stress_before': 0.382975, 'mean_grid_stress_after': 0.374178, 'estimated_carbon_saving_kgco2': 1.4774}`
- whether schema file was found: `True`
- whether output JSON parsed successfully: `True`

## Exact Command Used

```bash
python apps/dgx_pipeline/src/generate_demo_response.py --predictions data/processed/grid_stress_predictions.csv --output data/mock/gridflex_demo_response_dgx.json
```
