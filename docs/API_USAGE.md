# GridFlex API Usage

## Start The API

Optional hosted NVIDIA text explanations use the OpenAI-compatible client. This repo does not currently have a Python requirements file, so install it manually when enabling that path:

```bash
pip install openai
```

On DGX:

```bash
cd ~/gridflex-compute
. .venv-dgx/bin/activate
uvicorn apps.api.app.main:app --host 0.0.0.0 --port 8000
```

On another machine with FastAPI and Uvicorn available:

```bash
uvicorn apps.api.app.main:app --host 0.0.0.0 --port 8000
```

## Endpoint List

- `GET /health`
- `GET /api/v1/demo`
- `GET /api/v1/demo-coord`
- `GET /api/v1/demo-dgx`
- `GET /api/v1/demo-original`
- `GET /api/v1/live-carbon`
- `GET /api/v1/nim-status`
- `POST /api/v1/explain-decision`
- `GET /api/v1/kpis`
- `GET /api/v1/decisions`
- `GET /api/v1/grid-windows`
- `GET /metrics`

## Active Payload Behaviour

`/api/v1/demo` returns the DGX payload by default when `data/mock/gridflex_demo_response_dgx.json` is present and valid. If that file is missing or invalid, it falls back to `data/mock/gridflex_demo_response.json`.

Use the explicit endpoints when needed:

- `/api/v1/demo-dgx` for DGX payload only
- `/api/v1/demo-original` for the original mock payload only

## Example UI Fetch

```javascript
const response = await fetch('http://localhost:8000/api/v1/demo');
const data = await response.json();
```

## Example KPI Fetch

```javascript
const response = await fetch('http://localhost:8000/api/v1/kpis');
const kpis = await response.json();
```

## Example Live Carbon Fetch

```javascript
const response = await fetch('http://localhost:8000/api/v1/live-carbon');
const liveCarbon = await response.json();
```

If the NESO API is unavailable, the endpoint returns a safe fallback response and GridFlex should continue using the existing forecast workflow.

## Example NIM Status Fetch

```javascript
const response = await fetch('http://localhost:8000/api/v1/nim-status');
const nimStatus = await response.json();
```

## Example NIM Explanation Request

```javascript
const response = await fetch('http://localhost:8000/api/v1/explain-decision', {
	method: 'POST',
	headers: { 'Content-Type': 'application/json' },
	body: JSON.stringify({
		job_id: 'job-001',
		decision: 'shifted',
		reason_code: 'GRID_STRESS_AVOIDANCE',
		grid_stress_before: 0.72,
		grid_stress_after: 0.41,
		delay_minutes: 120,
		deadline_protected: true,
		carbon_signal: 'low',
		workload_type: 'batch_inference',
	}),
});
const explanation = await response.json();
```

If `NVIDIA_API_KEY` is missing or the hosted request fails, the endpoint returns deterministic fallback text and the rest of GridFlex remains unaffected.

## Example Prometheus Scrape Target

If Prometheus runs on the same machine as the API, use:

```yaml
- targets: ["localhost:8000"]
```

If Prometheus runs on another machine, replace `localhost` with the host or IP where the FastAPI app is reachable.

## Smoke Test

```bash
python apps/api/test_api_smoke.py --base-url http://localhost:8000
```