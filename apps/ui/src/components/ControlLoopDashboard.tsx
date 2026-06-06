"use client";

import { useState } from "react";
import Link from "next/link";

import type {
  ControlLoopDemoResponse,
  DemoReadinessResponse,
  GpuPulseDemoResponse,
} from "@/types/gridflex";

type ControlLoopDashboardProps = {
  controlLoop: ControlLoopDemoResponse | null;
  readiness: DemoReadinessResponse | null;
  apiBaseUrl?: string | null;
  error?: string | null;
};

const DEFAULT_API_BASE_URL = "http://scan-12.local:8000";

function normalizeBaseUrl(apiBaseUrl?: string | null) {
  return (apiBaseUrl?.trim() || DEFAULT_API_BASE_URL).replace(/\/$/, "");
}

function formatWorkloadType(value: string) {
  return value.replaceAll("_", " ");
}

function formatBooleanState(value: boolean) {
  return value ? "ready" : "not ready";
}

function formatUtcDateTime(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  const day = String(date.getUTCDate()).padStart(2, "0");
  const month = String(date.getUTCMonth() + 1).padStart(2, "0");
  const year = date.getUTCFullYear();
  const hours = String(date.getUTCHours()).padStart(2, "0");
  const minutes = String(date.getUTCMinutes()).padStart(2, "0");
  const seconds = String(date.getUTCSeconds()).padStart(2, "0");

  return `${day}/${month}/${year}, ${hours}:${minutes}:${seconds} UTC`;
}

function formatJson(value: unknown) {
  return JSON.stringify(value, null, 2);
}

function StatusCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="status-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function ReadinessItem({ label, value }: { label: string; value: boolean }) {
  return (
    <div className="readiness-item">
      <span>{label}</span>
      <span className={`pill ${value ? "ok" : "fallback"}`}>{formatBooleanState(value)}</span>
    </div>
  );
}

export function ControlLoopDashboard({ controlLoop, readiness, apiBaseUrl, error }: ControlLoopDashboardProps) {
  const [pulseResult, setPulseResult] = useState<GpuPulseDemoResponse | null>(null);
  const [pulseError, setPulseError] = useState<string | null>(null);
  const [runningPulse, setRunningPulse] = useState(false);

  async function handleRunGpuPulse() {
    setRunningPulse(true);
    setPulseError(null);

    try {
      const response = await fetch(`${normalizeBaseUrl(apiBaseUrl)}/api/v1/gpu-pulse-demo`, {
        method: "POST",
        cache: "no-store"
      });

      if (!response.ok) {
        throw new Error(`GPU pulse request failed with status ${response.status}`);
      }

      const payload = (await response.json()) as GpuPulseDemoResponse;
      setPulseResult(payload);
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : String(caughtError);
      setPulseError(message);
      setPulseResult(null);
    } finally {
      setRunningPulse(false);
    }
  }

  if (!controlLoop || !readiness) {
    return (
      <main className="shell">
        <div className="page-nav button-row">
          <Link className="button" href="/dashboard">
            Back to GridFlex Dashboard
          </Link>
        </div>

        <section className="hero">
          <div>
            <p className="eyebrow">control loop demo</p>
            <h1>Live AI-factory control loop</h1>
            <p className="lede">This additive page keeps the main dashboard intact and adds a control-loop story driven by live carbon, readiness, and a manual GPU pulse.</p>
          </div>
        </section>

        <section className="panel" aria-live="polite">
          <strong>Control-loop dashboard unavailable</strong>
          <p>{error ?? "The control-loop API routes are not currently reachable."}</p>
        </section>
      </main>
    );
  }

  const liveSignal = controlLoop.live_carbon_signal;
  const incomingJob = controlLoop.sample_incoming_ai_training_job;

  return (
    <main className="shell">
      <div className="page-nav button-row">
        <Link className="button" href="/dashboard">
          Back to GridFlex Dashboard
        </Link>
      </div>

      <section className="hero">
        <div>
          <p className="eyebrow">control loop demo</p>
          <h1>Real-time AI training admission and DGX pulse control</h1>
          <p className="lede">This page combines live carbon, coordination readiness, optional NIM explanation, and a manual GPU pulse into a single operator-facing control loop.</p>
        </div>
        <aside className="meta-card">
          Active payload
          <strong>{controlLoop.active_payload}</strong>
          <br />
          Decision
          <strong>{formatWorkloadType(controlLoop.decision)}</strong>
          <br />
          Endpoint
          <strong>{apiBaseUrl ?? "Unavailable"}</strong>
        </aside>
      </section>

      <section className="panel live-carbon-card" aria-live="polite">
        <div className="live-carbon-header">
          <div>
            <h2>Control-loop decision</h2>
            <p className="panel-subtitle">{controlLoop.reason}</p>
          </div>
          <span className={`pill ${controlLoop.decision}`}>{formatWorkloadType(controlLoop.decision)}</span>
        </div>

        <div className="status-grid">
          <StatusCard label="Live carbon" value={typeof liveSignal.current_intensity === "number" ? `${liveSignal.current_intensity} gCO2/kWh` : "Unavailable"} />
          <StatusCard label="Energy shifted" value={`${controlLoop.estimated_energy_shifted_kwh} kWh`} />
          <StatusCard label="Incoming job" value={incomingJob.job_id} />
        </div>

        <div className="voice-ready-box">
          <strong>Operator explanation</strong>
          <p>{controlLoop.operator_message}</p>
        </div>
      </section>

      <section className="control-loop-grid">
        <div>
          <section className="panel">
            <h2>Incoming AI training job</h2>
            <div className="table-wrap">
              <table>
                <tbody>
                  <tr><th>Job ID</th><td>{incomingJob.job_id}</td></tr>
                  <tr><th>Tenant</th><td>{incomingJob.tenant}</td></tr>
                  <tr><th>Type</th><td>{formatWorkloadType(incomingJob.workload_type)}</td></tr>
                  <tr><th>GPUs</th><td>{incomingJob.gpu_count}</td></tr>
                  <tr><th>Duration</th><td>{incomingJob.duration_minutes} min</td></tr>
                  <tr><th>Energy</th><td>{incomingJob.estimated_energy_kwh} kWh</td></tr>
                  <tr><th>Urgency</th><td>{incomingJob.urgency_class}</td></tr>
                  <tr><th>Deadline</th><td>{formatUtcDateTime(incomingJob.deadline_at)}</td></tr>
                </tbody>
              </table>
            </div>
          </section>

          <div style={{ height: 18 }} />

          <section className="panel">
            <h2>Component sources</h2>
            <div className="source-chip-row">
              <div className="source-chip"><span>Live carbon</span><strong>{controlLoop.component_sources.live_carbon}</strong></div>
              <div className="source-chip"><span>Coordination API</span><strong>{controlLoop.component_sources.coordination_api}</strong></div>
              <div className="source-chip"><span>Nemotron</span><strong>{controlLoop.component_sources.nemotron}</strong></div>
              <div className="source-chip"><span>DGX payload</span><strong>{controlLoop.component_sources.dgx_payload}</strong></div>
            </div>
          </section>

          <div style={{ height: 18 }} />

          <section className="panel pulse-panel">
            <div className="live-carbon-header">
              <div>
                <h2>Manual GPU pulse</h2>
                <p className="panel-subtitle">Runs only on button click. It never starts automatically when the page loads.</p>
              </div>
              <span className={`pill ${controlLoop.component_sources.gpu_pulse.gpu_pulse_enabled ? "enabled" : "disabled"}`}>
                {controlLoop.component_sources.gpu_pulse.gpu_pulse_enabled ? "enabled" : "disabled"}
              </span>
            </div>

            <div className="pulse-metrics">
              <StatusCard label="nvidia-smi" value={controlLoop.component_sources.gpu_pulse.nvidia_smi_available ? "available" : "missing"} />
              <StatusCard label="nvcc" value={controlLoop.component_sources.gpu_pulse.nvcc_available ? "available" : "missing"} />
              <StatusCard label="numpy" value={controlLoop.component_sources.gpu_pulse.numpy_available ? "available" : "missing"} />
            </div>

            <div className="button-row">
              <button className="button primary" type="button" onClick={handleRunGpuPulse} disabled={runningPulse}>
                {runningPulse ? "Running GPU Pulse..." : "Run Manual GPU Pulse"}
              </button>
            </div>

            {pulseError ? (
              <div className="voice-ready-box">
                <strong>Pulse error</strong>
                <p>{pulseError}</p>
              </div>
            ) : null}

            {pulseResult ? (
              <div className="pulse-result">
                <strong>Pulse response</strong>
                <pre>{formatJson(pulseResult)}</pre>
              </div>
            ) : null}
          </section>
        </div>

        <div>
          <section className="panel">
            <h2>Demo readiness</h2>
            <div className="readiness-list">
              <ReadinessItem label="DGX backend" value={readiness.dgx_backend_ready} />
              <ReadinessItem label="Demo payload" value={readiness.demo_payload_ready} />
              <ReadinessItem label="Live carbon" value={readiness.live_carbon_ready} />
              <ReadinessItem label="Coordination API public" value={readiness.coordination_api_ready_public} />
              <ReadinessItem label="NIM configured" value={readiness.nim_configured} />
              <ReadinessItem label="GPU pulse enabled" value={readiness.gpu_pulse_enabled} />
              <ReadinessItem label="Metrics" value={readiness.metrics_ready} />
            </div>
          </section>

          <div style={{ height: 18 }} />

          <section className="panel">
            <h2>Source flags</h2>
            <div className="readiness-list">
              <ReadinessItem label="Live carbon used" value={controlLoop.sources.live_carbon_used} />
              <ReadinessItem label="Coordination API used" value={controlLoop.sources.coordination_api_used} />
              <ReadinessItem label="Coordination fallback" value={controlLoop.sources.coordination_api_fallback} />
              <ReadinessItem label="Nemotron used" value={controlLoop.sources.nemotron_used} />
              <ReadinessItem label="Nemotron fallback" value={controlLoop.sources.nemotron_fallback} />
              <ReadinessItem label="DGX payload used" value={controlLoop.sources.dgx_payload_used} />
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}