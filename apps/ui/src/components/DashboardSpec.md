# Madhav UI Build Spec

## Required views
1. KPI strip: Jobs shifted, peak kWh avoided, GPU utilisation preserved, deadline miss rate.
2. Timeline: 24 half-hour grid windows with stress band.
3. Workload queue: job id, tenant, workload type, urgency, GPU count, decision.
4. Decision explanation: NIM-generated sentence for each shifted job.
5. Before/after comparison: stress before vs scheduled stress.

## API source
Use mock_api/gridflex_demo_response.json first. Later switch to /api/v1/demo.
