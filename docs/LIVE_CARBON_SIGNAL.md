# Live Carbon Signal

## Purpose

GridFlex can optionally surface a live carbon signal alongside its DGX-trained grid forecast so operators can demonstrate a simple Emerald AI-style sustainability control loop without changing the existing scheduler workflow.

## Data source

- Public source: https://api.carbonintensity.org.uk/intensity
- Provider: NESO Carbon Intensity API for Great Britain

## Backend endpoint

- `GET /api/v1/live-carbon`

The route uses a short timeout and does not require secrets.

## Response behavior

On success, the backend returns the latest current carbon intensity, a normalized recommendation, and a voice-ready operator explanation.

On failure, the backend returns a safe fallback payload and tells the operator to use the existing GridFlex forecast instead.

Example fallback response:

```json
{
  "status": "fallback",
  "source": "fallback",
  "current_intensity": null,
  "index": "unknown",
  "recommendation": "use_gridflex_forecast",
  "reason": "Live carbon signal unavailable; using GridFlex DGX-trained forecast instead."
}
```

## Recommendation mapping

- `<= 180`: `run_now`
- `181-300`: `run_selective`
- `> 300`: `delay_flexible_jobs`
- Unknown or unavailable: `use_gridflex_forecast`

## Dashboard support

The dashboard may display a compact Live Carbon Signal card that fetches the backend route after render. This keeps the existing GridFlex dashboard responsive and fallback-safe.

## Emerald AI-style demonstration value

This gives operators a live external sustainability cue that complements the existing GridFlex forecast and coordination demo paths.

- The live carbon signal shows the current grid carbon condition.
- The GridFlex DGX-trained forecast remains the primary safe scheduling fallback.
- The operator message can later be reused for NIM or Riva voice narration.

## Training requirement

No additional model training is required for this feature.