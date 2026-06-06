# GridFlex Compute v2

Grid-aware scheduling for flexible AI/GPU workloads.

## Demo thesis
AI compute is flexible demand. GridFlex shifts non-urgent GPU jobs away from stressed electricity windows while preserving deadlines and GPU utilisation.

## Main services
- apps/api: FastAPI admission and scheduling API.
- apps/ui: React/Next.js command centre.
- apps/dgx_pipeline: RAPIDS/cuDF/cuML data pipeline for DGX.
- packages/contracts: shared JSON schemas.
- infra/prometheus and infra/grafana: observability demo.
