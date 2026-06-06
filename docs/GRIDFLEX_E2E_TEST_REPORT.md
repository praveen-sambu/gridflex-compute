# GridFlex E2E Test Report

## Test Timestamp

- 2026-06-06 17:12:34 +01:00

## Runtime Targets

- Backend URL: `http://scan-12.local:8000`
- UI URL: `http://localhost:3001/dashboard`
- Hosted coordination API URL: `https://amartyagroup.com/coordination-api`

## Secret Scan Result

- `.env` is ignored by git.
- Broad keyword scan found documentation and placeholder references only.
- Narrow high-signal secret scan on changed files found no credential-like values.

## UI Build Result

- `npm run build` passed.
- Next.js emitted a non-fatal tracing warning from `apps/ui/next.config.ts`.
- `apps/ui/next-env.d.ts` remains a build-generated file.

## Endpoint Status

| Component | URL | Status | Key fields |
| --- | --- | --- | --- |
| Backend health | `http://scan-12.local:8000/health` | PASS | `status=ok`, `active_payload=dgx` |
| Demo | `http://scan-12.local:8000/api/v1/demo` | PASS | `run_id=dgx-demo-run-001`, `jobs_total=36`, `decisions=36` |
| KPIs | `http://scan-12.local:8000/api/v1/kpis` | PASS | `jobs_total=36`, `jobs_shifted=15`, `peak_kwh_avoided=3.5173` |
| Decisions | `http://scan-12.local:8000/api/v1/decisions` | PASS | `count=36` |
| Grid windows | `http://scan-12.local:8000/api/v1/grid-windows` | PASS | `count=36` |
| Live carbon | `http://scan-12.local:8000/api/v1/live-carbon` | PASS | `status=ok`, `current_intensity=84.0`, `index=low`, `recommendation=run_now` |
| Demo coord | `http://scan-12.local:8000/api/v1/demo-coord` | FALLBACK | `coordination_kernel_status=fallback`, `scheduler_mode=gridflex-v2` |
| NIM status | `http://scan-12.local:8000/api/v1/nim-status` | FALLBACK | `nim_enabled=false`, `api_key_available=false`, `mode=fallback` |
| Explain decision | `http://scan-12.local:8000/api/v1/explain-decision` | FALLBACK | `source=fallback`, `operator_message present`, `fallback_reason=null`, `provider_latency_ms=null` |
| Metrics | `http://scan-12.local:8000/metrics` | PASS | `gridflex_jobs_total` present |
| Coordination root | `https://amartyagroup.com/coordination-api/` | PASS | HTTP 200 |
| Coordination health | `https://amartyagroup.com/coordination-api/health` | PASS | HTTP 200 |
| Coordination docs | `https://amartyagroup.com/coordination-api/docs` | PASS | HTTP 200 |
| Coordination openapi | `https://amartyagroup.com/coordination-api/openapi.json` | PASS | HTTP 200 |

## NIM Status

- Local direct probe in `scripts/probe_nvidia_nim.py` reached NVIDIA successfully.
- DGX runtime remains fallback-safe because no NVIDIA API key is configured server-side on DGX.
- Fallback remains an acceptable demo outcome because `operator_message` is returned and `/api/v1/demo` is unaffected.

## Live Carbon Status

- The DGX backend live carbon route returned live NESO data during this pass.
- The UI dashboard showed the live carbon card with current intensity, index, recommendation, and voice-ready explanation.

## UI Runtime Status

- The dashboard route loaded at `http://localhost:3001/dashboard`.
- The page showed KPI cards, workload queue, decision table, decision explanations, and the live carbon card.
- The dashboard reported it was connected to `http://scan-12.local:8000/api/v1/demo`.

## Known Caveats

- `https://coordination-api.aayusuite.com` still returns Cloudflare 525.
- The public working coordination API route is `https://amartyagroup.com/coordination-api`.
- NVIDIA NIM may fall back if the provider is unavailable or if no NVIDIA key is configured on the serving backend.
- `/api/v1/demo` remains the stable judging route.
