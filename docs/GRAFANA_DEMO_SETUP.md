# GridFlex Grafana Demo Setup

This setup assumes the GridFlex backend API is already running on DGX and serving metrics at `http://scan-12.local:8000/metrics`.

## 1. Test the metrics endpoint

From Windows PowerShell:

```powershell
curl.exe http://scan-12.local:8000/metrics
```

You should see Prometheus text output with metrics such as:

- `gridflex_jobs_total`
- `gridflex_jobs_shifted_total`
- `gridflex_jobs_admitted_now_total`
- `gridflex_gpu_utilisation_preserved_pct`
- `gridflex_grid_stress_before`
- `gridflex_grid_stress_after`
- `gridflex_deadline_miss_rate`
- `gridflex_estimated_carbon_saving_kgco2`
- `gridflex_dgx_payload_available`

## 2. Run Prometheus locally

If Prometheus is already installed locally, run it from the repo root with the demo scrape config:

```powershell
prometheus --config.file="infra/prometheus/prometheus.gridflex-demo.yml"
```

Default Prometheus UI:

```text
http://localhost:9090
```

## 3. Prometheus scrape target

The demo config scrapes this exact target:

```text
scan-12.local:8000
```

The config file is:

- `infra/prometheus/prometheus.gridflex-demo.yml`

If you prefer to add the job to an existing Prometheus instance, use:

```yaml
scrape_configs:
  - job_name: "gridflex-api-dgx-demo"
    metrics_path: /metrics
    static_configs:
      - targets: ["scan-12.local:8000"]
```

## 4. Add Prometheus as a Grafana datasource

In Grafana:

1. Open `Connections` > `Data sources`
2. Add a `Prometheus` datasource
3. Set the URL to:

```text
http://localhost:9090
```

4. Save and test the datasource

## 5. Import the GridFlex dashboard JSON

Import this file into Grafana:

- `infra/grafana/gridflex_demo_dashboard.json`

Dashboard title:

```text
GridFlex Compute v2 - DGX Demo
```

## 6. Expected dashboard panels

The imported dashboard includes:

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

For the current demo payload, you should see values close to:

- `Jobs Total`: `36`
- `Jobs Shifted`: `15`
- `Jobs Admitted Now`: `21`
- `GPU Utilisation Preserved`: `97.08`
- `Peak kWh Avoided`: `3.5173`
- `Estimated Carbon Saving`: `1.4774`
- `Deadline Miss Rate`: `0`
- `Shift Ratio`: `0.4167`
- `DGX Payload Available`: `1`

## 7. If `scan-12.local` does not resolve

Fetch the DGX IP address:

```powershell
ssh nvidia@scan-12.local 'hostname -I'
```

Then replace the scrape target with:

```text
<DGX-IP>:8000
```

and test metrics directly with:

```powershell
curl http://<DGX-IP>:8000/metrics
```

If needed, make the same substitution in your Grafana Prometheus data source so Grafana and Prometheus both point at the reachable DGX host.

## 8. Quick validation flow

1. Confirm `http://scan-12.local:8000/metrics` is reachable.
2. Start Prometheus with `infra/prometheus/prometheus.gridflex-demo.yml`.
3. Open Prometheus at `http://localhost:9090` and confirm the target is `UP`.
4. Open Grafana and import `infra/grafana/gridflex_demo_dashboard.json`.
5. Confirm the dashboard panels show live values from the DGX demo backend.