# GridFlex Compute v2 - High Level Design

## 1. Purpose
GridFlex Compute v2 is a grid-aware AI workload scheduler. It treats non-urgent GPU jobs as flexible demand and schedules them into lower grid-stress windows while protecting workload deadlines and GPU utilisation.

## 2. Hackathon demo scope
The demo compares two scheduling modes:
- Baseline: run jobs immediately or at first available GPU slot.
- GridFlex v2: run urgent jobs immediately; shift flexible jobs to lower-stress, lower-cost, or lower-carbon windows where the deadline allows.

## 3. Data inputs
- LCL smart meter file: half-hour household consumption data used to derive a demand/stress proxy.
- UKPN Flexibility Dispatches metadata: confirms actual dispatch data exists but access may require registration/login.
- Synthetic AI workload queue: generated jobs with GPU count, energy, urgency and deadline.
- Optional carbon/tariff inputs: used as secondary scoring features.

## 4. NVIDIA usage story
The DGX is used for GPU-native data and model work:
- cuDF: load and aggregate large half-hourly consumption data.
- Dask-cuDF: scale the processing if the full 1.4 GB file is used.
- cuML: train a stress-band classifier or regressor.
- NIM: generate human-readable decision explanations.
- Triton/NIM optional: serve the stress prediction model or explanation model as an inference service.
- Nsight / DCGM exporter optional: show GPU utilisation and prove DGX resources are being used efficiently.

## 5. Components
### API layer
FastAPI exposes /api/v1/demo, /api/v1/schedule, /metrics and /health.

### Coordination kernel boundary
The coordination kernel remains private. It is wrapped behind a narrow API adapter. The UI never calls the kernel directly.

### DGX pipeline
The DGX pipeline creates grid_stress_profile_from_lcl.csv and optionally produces next-window stress forecasts.

### UI
The UI shows the operational command centre: KPIs, grid timeline, workload decisions, and explanation strings.

### Observability
Prometheus scrapes /metrics. Grafana shows shifted jobs, peak kWh avoided, stress before/after, deadline miss rate and GPU utilisation preserved.

## 6. API contract
The response contains:
- kpis
- grid_windows
- workloads
- decisions
- NIM explanation per decision

## 7. Safety boundary
Do not expose proprietary optimisation logic or coordination kernel internals. Only expose decisions, metrics and reason codes.
