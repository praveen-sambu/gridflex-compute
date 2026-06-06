# Coordination Kernel Integration

GridFlex can optionally call an external coordination kernel API from the backend without changing the default demo flow.

**Architecture**

GridFlex Backend -> hosted coordination-kernel API -> private kernel adapter

The backend acts as a thin adapter: it sends `grid_windows` and `workloads` to the hosted coordination API and, on success, replaces the `kpis` and `decisions` in the active demo payload with the kernel's response.

## Hosted coordination API

- Public base URL: https://amartyagroup.com/coordination-api
- Valid test routes:
  - https://amartyagroup.com/coordination-api/
  - https://amartyagroup.com/coordination-api/health
  - https://amartyagroup.com/coordination-api/docs
- Protected scheduling endpoint (POST): https://amartyagroup.com/coordination-api/v1/schedule
- Auth header: `X-API-Key: <server-side key>` (server-side only; do not expose to frontend)

> Operational caveat: the public coordination API is hosted under the `/coordination-api/` prefix on `amartyagroup.com`.

## Environment variables (server-side only)

These are backend-only values. Never expose them to the frontend or commit real keys.

```text
COORD_KERNEL_ENABLED=true
COORD_KERNEL_API_URL=https://amartyagroup.com/coordination-api
COORD_KERNEL_API_KEY=<do-not-commit-real-key>
```

## Endpoint behavior

- `GET /api/v1/demo` keeps the current GridFlex behavior and never calls the coordination kernel.
- `GET /api/v1/demo-coord` loads the active DGX or mock payload, sends `grid_windows` and `workloads` to `POST /v1/schedule`, and only replaces `kpis` and `decisions` if the external API returns valid data.
- If the coordination kernel is disabled, misconfigured, unreachable, times out, or returns invalid data, `GET /api/v1/demo-coord` falls back to the normal demo payload and adds:

```json
{
  "coordination_kernel_status": "fallback"
}
```

## Request shape sent to the coordination kernel

```json
{
  "grid_windows": [...],
  "workloads": [...]
}
```

The backend sends the API key in the `X-API-Key` header and uses a ~3 second timeout by default.

## Expected response shape from the coordination kernel

The adapter accepts a JSON object that contains valid `kpis` (object) and `decisions` (list) either at the top level or under `payload`, `result`, or `data`.

Example:

```json
{
  "kpis": {"jobs_total": 36},
  "decisions": [{"job_id": "job-2000", "decision": "shifted"}]
}
```

## Notes

- Do not use `https://coordination-api.aayusuite.com` for now — that host currently returns Cloudflare/TLS errors (525) and is not reliable until DNS/TLS is fixed.
- Local DGX URL (optional when running kernel on DGX): `http://scan-12.local:8100`

## Smoke test

Run the existing smoke script against a local API instance:

```powershell
python apps/api/test_api_smoke.py --base-url http://localhost:8000
```

## Manual curl checks

```powershell
curl http://localhost:8000/api/v1/demo
curl http://localhost:8000/api/v1/demo-coord
curl https://amartyagroup.com/coordination-api/health
```