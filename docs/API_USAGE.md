# GridFlex API Usage

## Start The API

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
- `GET /api/v1/demo-dgx`
- `GET /api/v1/demo-original`
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