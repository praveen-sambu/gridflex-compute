# Carbon Orchestration Demo

## Purpose

This additive demo route shows a second GridFlex story: whether AI training and inference jobs should run now, wait, or request a cleaner resource window based on live UK carbon intensity.

## Difference From The Main Dashboard

The main GridFlex dashboard uses the existing DGX-trained stress model and workload scheduling payload served from `/api/v1/demo`.

The live carbon orchestration route uses the NESO Carbon Intensity signal from `/api/v1/live-carbon` and applies a lightweight policy layer for a synthetic AI workload queue. It does not replace the main DGX demo and does not modify its behavior.

## No Retraining Required

No model retraining is required for this route. The new endpoint reuses the existing live carbon integration and applies a simple orchestration policy to synthetic workloads.

## Emerald AI-Style Story Support

This route supports an Emerald AI-style story because it turns a live carbon signal into immediate operational guidance for AI workloads. It demonstrates how a platform can translate a real-time sustainability signal into a workload admission decision that an operator can explain and act on.

## NVIDIA GPU Positioning

This helps NVIDIA GPU positioning because it frames GPU clusters as schedulable, policy-aware infrastructure. The story is not only about raw acceleration; it also shows how operators can place training and inference workloads into lower-carbon windows, preserve urgent throughput, and expose decision logic to customers, FinOps teams, and sustainability stakeholders.