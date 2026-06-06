# Control Loop Demo

This demo adds a small live AI-factory control loop on top of the existing GridFlex demo surfaces.

## Purpose

- Main dashboard: learned DGX scheduling and the existing GridFlex demo payload.
- Control-loop page: real-time orchestration using live carbon, optional coordination API input, optional Nemotron explanation, and a manually triggered DGX pulse.
- GPU pulse: bounded, operator-triggered only, and safe to run in a demo environment.

## Endpoints

- `GET /api/v1/control-loop-demo`
  - Returns one incoming AI training job, the live carbon signal, the orchestration decision, operator explanation, estimated shifted energy, and component source fields.
- `POST /api/v1/gpu-pulse-demo`
  - Runs only when `ENABLE_GPU_PULSE_DEMO=true`.
  - Returns `{"status":"disabled","message":"GPU pulse disabled by environment"}` when disabled.
  - When enabled, runs a small bounded workload and returns timestamps, duration, backend used, safety limit, and optional `nvidia-smi` snapshots.
- `GET /api/v1/demo-readiness`
  - Returns compact readiness flags for DGX backend, payload availability, live carbon, public coordination API configuration, Nemotron readiness, GPU pulse enablement, and metrics availability.

## UI surfaces

- `/dashboard`
  - Keeps the learned DGX scheduling framing and links to the live control-loop view.
- `/dashboard/control-loop`
  - Shows the incoming job, live carbon, decision, operator explanation, component badges, readiness flags, and manual pulse controls.

## Safety constraints

- The existing `/api/v1/demo` endpoint remains unchanged.
- The control-loop endpoint is additive and does not run the GPU pulse automatically.
- The GPU pulse is bounded to a maximum of five seconds and is intended as a safe DGX signal, not a stress test.
- Nemotron is optional. If no hosted NVIDIA configuration is available, GridFlex falls back to a safe local explanation.
- Coordination API usage is optional. If not configured, the demo falls back to the local GridFlex policy and payload data.