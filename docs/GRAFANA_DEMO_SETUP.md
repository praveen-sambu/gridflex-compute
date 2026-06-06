# GridFlex Grafana Demo Setup

This observability layer is optional. It should sit beside the GridFlex demo, not become a dependency for `/api/v1/demo` or the main presentation flow.

## 1. Choose the scrape target

Use one of these Prometheus targets:

- Local backend: `localhost:8000`
- Docker-to-local backend: `host.docker.internal:8000`
- DGX backend from the office network: `scan-12.local:8000`

Prometheus config files already in the repo:

- Local backend config: `infra/prometheus/prometheus.yml`
- DGX office-network config: `infra/prometheus/prometheus.gridflex-demo.yml`

## 2. Test the metrics endpoint first

From Windows PowerShell:

```powershell
curl.exe -s http://localhost:8000/metrics
```

If the DGX host is reachable from your current network:

```powershell
curl.exe -s http://scan-12.local:8000/metrics
```

You should see Prometheus text output with metrics such as:

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

## 3. Run Prometheus directly if it is installed locally

For a local backend on port `8000`:

```powershell
prometheus --config.file="infra/prometheus/prometheus.yml"
```

For the office DGX backend when `scan-12.local` resolves:

```powershell
prometheus --config.file="infra/prometheus/prometheus.gridflex-demo.yml"
```

Default Prometheus UI:

```text
http://localhost:9090
```

## 4. Run the optional Docker observability stack

If you do not have local Prometheus or Grafana binaries, use:

```powershell
$env:GRIDFLEX_SCRAPE_TARGET = 'host.docker.internal:8000'
docker compose -f infra/observability/docker-compose.observability.yml up -d
```

For the DGX backend instead:

```powershell
$env:GRIDFLEX_SCRAPE_TARGET = 'scan-12.local:8000'
docker compose -f infra/observability/docker-compose.observability.yml up -d
```

Expected URLs:

- Prometheus: `http://localhost:9091`
- Grafana: `http://localhost:3003`

Local demo login:

- Username: `admin`
- Password: `admin`

Port `9090` is commonly occupied by other local tools. This optional GridFlex stack uses host port `9091` for Prometheus specifically to avoid that conflict.

## 5. Grafana provisioning behavior

The optional Docker Compose stack now auto-provisions:

- Datasource: `GridFlex Prometheus`
- Dashboard: `GridFlex Compute v2 - DGX Demo`

The datasource points at:

```text
http://prometheus:9090
```

The dashboard is loaded automatically from the existing repo file:

- `infra/grafana/gridflex_demo_dashboard.json`

Manual import is no longer required for the local demo stack.

## 6. Add Prometheus as a Grafana datasource manually if needed

In Grafana:

1. Open `Connections` > `Data sources`
2. Add a `Prometheus` datasource
3. Set the URL to `http://prometheus:9090` when using the Docker Compose stack, or `http://localhost:9091` when Grafana is running outside Docker
4. Save and test the datasource

## 7. Import the GridFlex dashboard JSON manually if needed

Import this file into Grafana:

- `infra/grafana/gridflex_demo_dashboard.json`

Dashboard title:

```text
GridFlex Compute v2 - DGX Demo
```

## 8. Expected dashboard panels

The dashboard is built around these metrics:

1. `Jobs Total`
2. `Jobs Shifted`
3. `Jobs Admitted Now`
4. `GPU Utilisation Preserved`
5. `Peak kWh Avoided`
6. `Estimated Carbon Saving`
7. `Deadline Miss Rate`
8. `Shift Ratio`
9. `Grid Stress Before vs After`
10. `DGX Payload Available`

For the current demo payload, values should be close to:

- `Jobs Total`: `36`
- `Jobs Shifted`: `15`
- `Jobs Admitted Now`: `21`
- `GPU Utilisation Preserved`: `97.08`
- `Peak kWh Avoided`: `3.5173`
- `Estimated Carbon Saving`: `1.4774`
- `Deadline Miss Rate`: `0`
- `Shift Ratio`: `0.4167`
- `DGX Payload Available`: `1`

## 9. If the DGX host is not reachable from home

`scan-12.local` is an event or DGX-network hostname. It should only be used as a scrape target when you are on that network path. If it does not resolve from home, use the local backend path instead, or connect through the office VPN or another reachable DGX address before using the DGX scrape config.

## 10. Quick validation flow

1. Confirm either `http://localhost:8000/metrics` or `http://scan-12.local:8000/metrics` is reachable.
2. Start Prometheus directly or with `infra/observability/docker-compose.observability.yml`.
3. Open `http://localhost:3003` and sign in with `admin / admin` for the local demo stack.
4. Confirm the `GridFlex Prometheus` datasource is present.
5. Confirm the `GridFlex Compute v2 - DGX Demo` dashboard is present.
6. Confirm the panels show live values from the selected GridFlex backend.
