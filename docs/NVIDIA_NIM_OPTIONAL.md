# NVIDIA NIM Optional Integration

## Purpose
This note records what was verified from the DGX environment on 2026-06-06 and defines the current optional NVIDIA-hosted text explanation path for GridFlex.

Current status:
- `/api/v1/demo` remains unchanged.
- Live NVIDIA calls remain optional and server-side only.
- The existing demo keeps using static `nim_explanation` strings from the payload JSON.
- Text explanations can be requested through dedicated optional endpoints.

## Environment Summary
- Hostname: `scan-12`
- GPU: NVIDIA GB10 visible through `nvidia-smi`
- Docker CLI is installed, but `docker images` was not inspectable from this shell because access to `/var/run/docker.sock` is denied.
- `https://build.nvidia.com` is reachable from this DGX.
- `https://integrate.api.nvidia.com` is reachable at the network edge; a bare `HEAD` request returns `404`, which confirms connectivity but not a usable model route.
- No NVIDIA API key environment variables were set in the current shell.

## Hosted API Setup

GridFlex uses NVIDIA's OpenAI-compatible hosted API for optional text explanations.

- Base URL: `https://integrate.api.nvidia.com/v1`
- Model: `nvidia/nemotron-3-ultra-550b-a55b`
- Required server-side key variable: `NVIDIA_API_KEY`

Get the API key from build.nvidia.com or the associated NVIDIA hosted API entitlement flow, then set it outside the codebase. Do not commit keys.

This repo does not currently ship a Python requirements file, so install the client manually when enabling hosted explanations:

```bash
pip install openai
```

Recommended local environment variables:

- `NVIDIA_API_KEY=replace-with-build-nvidia-key`
- `NIM_BASE_URL=https://integrate.api.nvidia.com/v1`
- `NIM_MODEL=nvidia/nemotron-3-ultra-550b-a55b`
- `NIM_TIMEOUT_SECONDS=20`

Use shell exports, a local untracked env file, or a deployment secret store. Do not print the key, return it from the API, or expose it to frontend code.

## Endpoint List

- `GET /api/v1/nim-status`
- `POST /api/v1/explain-decision`

`/api/v1/demo` remains unchanged and does not call NVIDIA NIM.

## Nemotron Hosted Text Explanation Path

Because no NVIDIA API key was present in the local validation shell, only fallback behavior was exercised during the final test pass.

Current implementation behavior:
1. Read `NVIDIA_API_KEY` from the server environment only.
2. Use `https://integrate.api.nvidia.com/v1` unless `NIM_BASE_URL` overrides it.
3. Use `nvidia/nemotron-3-ultra-550b-a55b` unless `NIM_MODEL` overrides it.
4. Use `NIM_TIMEOUT_SECONDS`, defaulting to `20` seconds.
5. Generate a single operator-facing sentence with a short prompt and a small token budget.
6. Return deterministic fallback text if the key is missing, the `openai` package is unavailable, or the hosted request fails.
7. Keep `/api/v1/demo` non-blocking and unchanged.

Suggested future request payload for an explanation service:
- `job_id`
- `decision`
- `reason_code`
- `grid_stress_before`
- `grid_stress_after`
- `delay_minutes`
- `deadline_protected`

Current status response fields:
- `nim_enabled`
- `api_key_available`
- `model`
- `base_url`
- `mode`

Explanation response fields:
- `source`
- `model`
- `operator_message`
- `provider_latency_ms`
- `fallback_reason`

## Fallback Behavior
Current fallback behavior is already safe for the demo:
- `/api/v1/demo` serves the existing JSON payload.
- Each decision already contains a static `nim_explanation` string.
- No live NVIDIA dependency is required to render the dashboard.
- `GET /api/v1/nim-status` returns `mode=fallback` when the key is absent.
- `POST /api/v1/explain-decision` returns deterministic fallback text when the key is absent or the hosted call fails.
- `fallback_reason` is classified as `timeout`, `auth_error`, `rate_limit`, `api_error`, or `unknown_error` when the live provider call fails.
- Live provider timeouts do not break the demo; GridFlex still returns a safe explanation.

Example fallback pattern:
- Shifted jobs: `Shifted to a lower-stress grid window while protecting the deadline.`
- Immediate admission: `Admitted now because the current grid conditions or deadline constraints did not justify a delay.`

Do not propagate raw upstream errors to operators.

## Curl Examples

Do not paste real keys into committed files or shell history that will be shared.

Check status:

```bash
curl http://localhost:8000/api/v1/nim-status
```

Request an operator explanation:

```bash
curl -X POST http://localhost:8000/api/v1/explain-decision \
	-H "Content-Type: application/json" \
	-d '{
		"job_id": "job-001",
		"decision": "shifted",
		"reason_code": "GRID_STRESS_AVOIDANCE",
		"grid_stress_before": 0.72,
		"grid_stress_after": 0.41,
		"delay_minutes": 120,
		"deadline_protected": true,
		"carbon_signal": "low",
		"workload_type": "batch_inference"
	}'
```

## build.nvidia.com Note
Public build.nvidia.com content was reachable from this DGX and exposed Nemotron inference catalog content. That confirms public site access, not authenticated model entitlement.

Use build.nvidia.com or the hosted NIM endpoint only when all of the following are true:
- a valid API key is present,
- a specific text model has been selected,
- the request and response contract has been validated outside `/api/v1/demo`.

## Optional Speech Or TTS Path
This integration is text explanation only. Speech and voice were probed only.

What was observed:
- Public build.nvidia.com content includes speech- and Riva-related terms.
- No authenticated speech model endpoint or stable request contract was verified from this environment.
- No NVIDIA Riva, Triton, or NIM speech service was found running locally.
- Linux desktop `speech-dispatcher` processes were present, but they are not a GridFlex backend integration path.

Recommendation:
- Treat voice and TTS as future optional work.
- Do not make speech part of the demo critical path.
- Add it only after a concrete speech model, endpoint, and latency budget are confirmed.

## What Was Actually Tested
- `hostname`
- `nvidia-smi`
- `docker --version`
- `docker images | head` attempted, but Docker socket access was denied in this shell
- `python --version || python3 --version`
- redacted environment scan for `NVIDIA|NIM|NGC|API|BUILD`
- boolean presence checks for `NVIDIA_API_KEY`, `NGC_API_KEY`, `NIM_API_KEY`, `BUILD_NVIDIA_API_KEY`
- `curl -s -I https://build.nvidia.com`
- `curl -s -I https://integrate.api.nvidia.com`
- repo search for `NIM`, `Nemotron`, `NVIDIA_API_KEY`, `integrate.api.nvidia.com`, `operator_message`, and `nim_explanation`
- inspection of the FastAPI app and coordination-kernel adapter
- process check for local `uvicorn`, `nim`, `triton`, `riva`, `tts`, and `speech` services

## Validation Commands
- `python3 -m compileall /home/nvidia/gridflex-compute/apps/api/app`
- `curl http://scan-12.local:8000/api/v1/demo`
- `curl http://scan-12.local:8000/api/v1/nim-status`
- `curl -X POST http://scan-12.local:8000/api/v1/explain-decision -H "Content-Type: application/json" -d '{...}'`

Expected result today:
- `/api/v1/demo` returns `200`.
- `/api/v1/nim-status` returns `200` and reports `mode=fallback` until `NVIDIA_API_KEY` is configured server-side.
- `/api/v1/explain-decision` returns deterministic fallback text until `NVIDIA_API_KEY` is configured server-side.

## Backend Restart Command
The running API process on this DGX uses `apps.api.app.main:app` on port `8000` from `.venv-dgx`.

If the backend must be restarted after a future runtime change, use:

```bash
cd /home/nvidia/gridflex-compute
.venv-dgx/bin/python -m uvicorn apps.api.app.main:app --host 0.0.0.0 --port 8000
```