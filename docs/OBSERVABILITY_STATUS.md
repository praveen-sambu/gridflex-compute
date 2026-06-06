# GridFlex Observability Status

## Summary

- Metrics endpoint status: local backend reachable at `http://localhost:8000/metrics`
- DGX metrics status: not reliable from home because `scan-12.local` may not resolve outside the office network
- Prometheus config status: repo contains a valid local config and a DGX office-network config
- Grafana dashboard JSON status: valid JSON and auto-provisioned in the optional local stack
- Local install status:
  - Prometheus binary: not installed locally
  - Grafana binary: not installed locally
  - Existing Grafana service on `http://localhost:3000`: running, but it belongs to another local stack and should not be treated as GridFlex-owned observability
- Docker availability: available locally

## Verified Status

- `http://localhost:8000/metrics` returned live GridFlex metrics
- The following metric names were confirmed:
  - `gridflex_jobs_total`
  - `gridflex_jobs_shifted_total`
  - `gridflex_jobs_admitted_now_total`
  - `gridflex_peak_kwh_avoided`
  - `gridflex_gpu_utilisation_preserved_pct`
  - `gridflex_grid_stress_before`
  - `gridflex_grid_stress_after`
  - `gridflex_deadline_miss_rate`
  - `gridflex_estimated_carbon_saving_kgco2`
  - `gridflex_payload_available`
  - `gridflex_dgx_payload_available`
  - `gridflex_decision_shift_ratio`
- `infra/grafana/gridflex_demo_dashboard.json` parsed successfully as JSON

## Prometheus Config Status

- Local backend scrape config: `infra/prometheus/prometheus.yml`
  - Target: `localhost:8000`
- DGX office-network scrape config: `infra/prometheus/prometheus.gridflex-demo.yml`
  - Target: `scan-12.local:8000`

The local config is correct for home development when the backend is running on this machine. The DGX demo config is correct only when `scan-12.local` is reachable.

## Grafana Import File

- Exact import file: `infra/grafana/gridflex_demo_dashboard.json`

## Grafana Auto-Provisioning Status

- Datasource auto-provisioned: `GridFlex Prometheus`
- Dashboard auto-provisioned: `GridFlex Compute v2 - DGX Demo`
- Local demo login: `admin / admin`

## Optional Local Docker Stack

- Compose file: `infra/observability/docker-compose.observability.yml`
- Prometheus URL: `http://localhost:9091`
- Grafana URL: `http://localhost:3003`
- Configurable scrape target env var: `GRIDFLEX_SCRAPE_TARGET`
- Grafana datasource provisioning file: `infra/observability/grafana/provisioning/datasources/prometheus.yml`
- Grafana dashboard provider file: `infra/observability/grafana/provisioning/dashboards/gridflex.yml`

Example for local backend:

```powershell
$env:GRIDFLEX_SCRAPE_TARGET = 'host.docker.internal:8000'
docker compose -f infra/observability/docker-compose.observability.yml up -d
```

For the local demo stack, sign in at `http://localhost:3003` with `admin / admin`.

Example for DGX backend when reachable:

```powershell
$env:GRIDFLEX_SCRAPE_TARGET = 'scan-12.local:8000'
docker compose -f infra/observability/docker-compose.observability.yml up -d
```

## Local Install Status

- Prometheus executable: not found in `PATH`
- Grafana executable: not found in `PATH`
- Docker: available

## Local Port Caveats

- `3001` is in use by the GridFlex UI
- `3000` already serves a Grafana instance from another local stack
- `9090` is already bound by another local container on this machine
- The optional GridFlex Docker Compose stack therefore publishes Prometheus on `9091` instead

This means the optional Docker Compose observability stack can run without changing the existing local service on `9090`.

## DGX Reachability Caveat

From home or other non-office networks, `scan-12.local` may not resolve. It should be treated as an event or DGX-network-only scrape target unless you are on the right network path. In that case, the DGX scrape config will appear broken even though the dashboard and metric names are correct. Use the local backend path, office VPN, or another reachable DGX hostname or IP.

## Presentation Guidance

Use observability as an optional operations view, not as part of the main demo dependency chain.

Suggested presentation framing:

- The main GridFlex demo works independently of Prometheus and Grafana.
- The observability layer exposes the same scheduling KPIs through `/metrics` for operators.
- Grafana turns those KPIs into a live operations dashboard for jobs shifted, GPU utilisation preserved, grid stress, and carbon impact.
- If the DGX host is not reachable during the presentation, the same dashboard can still be shown against the local backend.
- For the local demo stack, Grafana and the GridFlex datasource are provisioned automatically so there is no manual setup step during the presentation.

## Current Assessment

The observability layer is presentation-ready as an optional operations view when one of these is true:

- the local backend is running and scraped locally, or
- the DGX host is reachable from the current network

The remaining blocker is environment-level, not application-level: this machine does not have native Prometheus or Grafana installed. The repo-local optional Docker Compose path avoids the existing `9090` conflict by using `http://localhost:9091` for Prometheus and `http://localhost:3003` for Grafana.