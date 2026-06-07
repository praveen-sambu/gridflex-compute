# GridFlex Hackathon Demo Script

## Current Recommended Demo Path

Use this route order for the safest live demo:

1. `/dashboard`
2. `/dashboard/live-carbon`
3. `/dashboard/voice-agent`
4. `http://localhost:3003` for Grafana

Use `/dashboard/control-loop` only if the DGX control-loop route is confirmed healthy immediately before recording.

## 90-Second Script

GridFlex is an orchestration layer for AI compute that helps training and inference workloads behave like better grid citizens.

Instead of sending every job straight to GPUs, GridFlex evaluates grid stress, workload urgency, carbon intensity, and GPU utilisation before deciding whether that work should run now or shift to a better window.

On the main dashboard, the first thing to look at is Grid Stress Impact. These are normalized average grid-stress scores on a 0 to 1 scale, where lower is better. In this run, average stress moves from 0.383 to 0.374, which is about a 2.3 percent reduction. That is a modest but real reduction in average stress, and the supporting KPIs show how that result is achieved through job shifting, peak energy avoidance, carbon savings, and zero deadline misses.

In the admission plane, incoming AI jobs enter on the left. In the middle, the GridFlex kernel evaluates stress thresholds, deadline protection, carbon-aware scheduling windows, and GPU preservation. On the right, jobs are either admitted into the DGX compute fabric or shifted into a cleaner queue.

The point is not to delay work blindly. The point is to make policy-aware scheduling decisions that protect throughput while reducing pressure on the grid.

The live carbon route extends that story by turning an external carbon signal into an operator recommendation: run now, run selectively, or delay flexible workloads until a cleaner window.

The voice-agent route shows the same system through a human interface. An operator can query the platform conversationally and get an explanation grounded in the same scheduling context.

Finally, Grafana gives the operations view: service health, metrics, and the telemetry layer behind the demo.

The headline is simple: GridFlex helps AI infrastructure reduce grid pressure and carbon impact without sacrificing operational discipline.

## 60-Second Version

GridFlex is a control layer for AI compute that decides whether workloads should run now or later based on grid stress, carbon intensity, urgency, and utilisation.

On the dashboard, the Grid Stress Impact section shows normalized average stress before and after scheduling. Here, the average stress score drops from 0.383 to 0.374, about 2.3 percent, while the KPI chips show the operational tradeoffs behind that result.

The admission plane makes the policy visible. Jobs come in on the left, the kernel evaluates them in the middle, and they are either admitted now or shifted to a cleaner operating window.

The live carbon and voice-agent routes show the same decision system through an operator-facing carbon workflow and a conversational interface.

## Click-by-Click Recording Flow

### 1. Main Dashboard

Say:

GridFlex is an AI workload orchestration layer for energy-aware compute scheduling.

Then point to:

- top status row
- Grid Stress Impact
- admission plane
- forecast timeline

### 2. Live Carbon Route

Say:

This route converts the live carbon signal into a clear operational recommendation for AI workloads.

Point to:

- current carbon guidance
- workload decision cards
- operator message

### 3. Voice Agent Route

Say:

This gives operators a natural-language interface into the same scheduling and decision context.

Point to:

- voice status
- session state
- explanation context

### 4. Grafana

Say:

Grafana gives the observability layer behind the demo, including service readiness and operations metrics.

## Presenter Notes

- Do not describe the stress chart as peak flattening unless you are showing a true peak-before and peak-after metric.
- Say "average grid stress" consistently.
- Keep repeating the same three-value message: reduce grid pressure, reduce carbon impact, preserve operational performance.
- If control-loop is still unstable, do not linger on it during the live presentation.

## Optional Control-Loop Line

If the route is healthy when you present:

This control-loop view shows the end-to-end admission pipeline, from incoming job to final action, using the same GridFlex policy logic.

If it is not healthy:

The control-loop route is part of the full system path, but for this recording we are focusing on the verified dashboard, live carbon, voice, and observability surfaces.