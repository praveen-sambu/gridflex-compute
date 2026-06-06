# Hosted Coordination API Status

- Hosted API base URL: https://amartyagroup.com/coordination-api

## Public route validation

- `https://amartyagroup.com/coordination-api/` -> HTTP 200
- `https://amartyagroup.com/coordination-api/health` -> HTTP 200
- `https://amartyagroup.com/coordination-api/docs` -> HTTP 200
- `https://amartyagroup.com/coordination-api/openapi.json` -> HTTP 200

## Protected routes

- `GET /v1/version` requires `X-API-Key`
- `POST /v1/schedule` requires `X-API-Key`
- Local validation shell did not have `COORD_KERNEL_API_KEY` set during the final clean pass, so protected hosted route tests were not performed.

## GridFlex environment variables

```text
COORD_KERNEL_ENABLED=true
COORD_KERNEL_API_URL=https://amartyagroup.com/coordination-api
COORD_KERNEL_API_KEY=<server-side-key>
```

## GridFlex backend validation

- `http://scan-12.local:8000/health` returned `status=ok`, `active_payload=dgx`, `dgx_payload_available=true`.
- `http://scan-12.local:8000/api/v1/demo` returned the DGX payload (`run_id=dgx-demo-run-001`, `jobs_total=36`, `decisions=36`).
- The currently deployed DGX backend returned HTTP 404 for `http://scan-12.local:8000/api/v1/demo-coord` during the clean final pass.
- Because no local API key was available, protected hosted API tests were skipped and the DGX backend was not restarted with hosted coordination settings.
- Existing observed behavior before this clean pass remained safe fallback on a backend version that included `/api/v1/demo-coord`: when coordination is unavailable or disabled, GridFlex returns the demo payload and sets `coordination_kernel_status` to `fallback`.

## Operational notes

- The public hosted coordination API is live behind the `/coordination-api/` prefix on `amartyagroup.com`.
- Do not use `https://coordination-api.aayusuite.com` yet; it still has Cloudflare 525 / TLS issues.
- No secrets were committed.
- No `.env` file was created or committed.

