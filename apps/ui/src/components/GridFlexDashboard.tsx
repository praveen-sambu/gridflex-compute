"use client";

import Link from "next/link";
import { Fragment, useEffect, useMemo, useState } from "react";

import type { Decision, GridFlexResponse, GridWindow, Workload } from "@/types/gridflex";

import { LiveCarbonSignalCard } from "@/components/LiveCarbonSignalCard";

type DashboardProps = {
  data: GridFlexResponse;
  dataSource: "api" | "mock";
  statusMessage?: string | null;
  apiBaseUrl?: string | null;
};

const timeFormatter = new Intl.DateTimeFormat("en-GB", {
  hour: "2-digit",
  minute: "2-digit",
  timeZone: "UTC"
});

function formatTime(value: string) {
  return timeFormatter.format(new Date(value));
}

function formatPct(value: number) {
  return `${value.toFixed(value % 1 === 0 ? 0 : 1)}%`;
}

function formatDecision(value?: string) {
  return value?.replaceAll("_", " ") ?? "pending";
}

function formatKwh(value: number) {
  return `${value.toFixed(value >= 10 ? 1 : 2)} kWh`;
}

function average(values: number[]) {
  if (values.length === 0) return 0;

  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function KpiCard({ label, value }: { label: string; value: string | number }) {
  return (
    <article className="kpi-card">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
    </article>
  );
}

function LiveTimestamp() {
  const [now, setNow] = useState<string | null>(null);

  useEffect(() => {
    const updateNow = () => setNow(new Date().toLocaleString());
    updateNow();

    const interval = window.setInterval(updateNow, 1000);

    return () => window.clearInterval(interval);
  }, []);

  return <strong>{now ?? "Syncing..."}</strong>;
}

function CapacityCard({ label, value, detail }: { label: string; value: string | number; detail: string }) {
  return (
    <article className="capacity-card">
      <div className="capacity-label">{label}</div>
      <strong>{value}</strong>
      <span>{detail}</span>
    </article>
  );
}

function GridTimeline({ windows }: { windows: GridWindow[] }) {
  return (
    <section className="panel">
      <h2>24 half-hour grid windows</h2>
      <div className="timeline" aria-label="Grid stress timeline">
        {windows.map((window) => (
          <div
            className="window-bar"
            key={window.timestamp}
            title={`${formatTime(window.timestamp)} · current ${window.grid_stress_score} · predicted ${window.predicted_grid_stress_score ?? window.grid_stress_score}`}
          >
            <div
              className={`bar ${window.stress_band}`}
              style={{ height: `${Math.max(window.grid_stress_score * 180, 18)}px` }}
            />
            <span className="time-label">{formatTime(window.timestamp)}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function WorkloadTable({ workloads, decisions }: { workloads: Workload[]; decisions: Decision[] }) {
  const decisionByJob = new Map(decisions.map((decision) => [decision.job_id, decision]));

  return (
    <section className="panel">
      <h2>Workload queue</h2>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Job</th>
              <th>Tenant</th>
              <th>Type</th>
              <th>GPUs</th>
              <th>Decision</th>
              <th>Scheduled</th>
            </tr>
          </thead>
          <tbody>
            {workloads.slice(0, 8).map((workload) => {
              const decision = decisionByJob.get(workload.job_id);

              return (
                <Fragment key={workload.job_id}>
                  <tr>
                    <td>{workload.job_id}</td>
                    <td>{workload.tenant}</td>
                    <td>{workload.workload_type.replaceAll("_", " ")}</td>
                    <td>{workload.gpu_count}</td>
                    <td>
                      <span className={`decision-badge ${decision?.decision ?? "pending"}`}>
                        <span aria-hidden="true" />
                        {formatDecision(decision?.decision)}
                      </span>
                    </td>
                    <td>{decision ? formatTime(decision.scheduled_start) : "—"}</td>
                  </tr>
                  <tr className="job-detail-row">
                    <td colSpan={6}>
                      <div className="job-detail-card">
                        <div>
                          <span>Deadline</span>
                          <strong>{formatTime(workload.deadline_at)}</strong>
                        </div>
                        <div>
                          <span>Duration</span>
                          <strong>{workload.duration_minutes} min</strong>
                        </div>
                        <div>
                          <span>Energy</span>
                          <strong>{formatKwh(workload.estimated_energy_kwh)}</strong>
                        </div>
                        <div>
                          <span>Urgency</span>
                          <strong>{workload.urgency_class}</strong>
                        </div>
                        {decision ? (
                          <p>
                            <strong>{decision.reason_code.replaceAll("_", " ")}: </strong>
                            {decision.nim_explanation}
                          </p>
                        ) : (
                          <p>No scheduler decision has been emitted yet.</p>
                        )}
                      </div>
                    </td>
                  </tr>
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function DecisionTable({ decisions }: { decisions: Decision[] }) {
  return (
    <section className="panel">
      <h2>Decision table</h2>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Job</th>
              <th>Decision</th>
              <th>Delay</th>
              <th>Before</th>
              <th>After</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            {decisions.slice(0, 8).map((decision) => (
              <tr key={decision.job_id}>
                <td>{decision.job_id}</td>
                <td>
                  <span className={`decision-badge ${decision.decision}`}>
                    <span aria-hidden="true" />
                    {formatDecision(decision.decision)}
                  </span>
                </td>
                <td>{decision.delay_minutes} min</td>
                <td>{decision.grid_stress_before.toFixed(3)}</td>
                <td>{decision.grid_stress_after.toFixed(3)}</td>
                <td>{decision.reason_code}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function AdmissionAlerts({ decisions, runId }: { decisions: Decision[]; runId: string }) {
  const admittedJobs = useMemo(
    () => decisions.filter((decision) => decision.decision === "admitted_now").slice(0, 2),
    [decisions]
  );
  const [visibleJobIds, setVisibleJobIds] = useState<string[]>(() => admittedJobs.map((decision) => decision.job_id));
  const [closingJobIds, setClosingJobIds] = useState<string[]>([]);

  const closeAlert = (jobId: string) => {
    setClosingJobIds((current) => (current.includes(jobId) ? current : [...current, jobId]));

    window.setTimeout(() => {
      setVisibleJobIds((current) => current.filter((visibleJobId) => visibleJobId !== jobId));
      setClosingJobIds((current) => current.filter((closingJobId) => closingJobId !== jobId));
    }, 900);
  };

  useEffect(() => {
    const timeouts = admittedJobs.map((decision) => window.setTimeout(() => closeAlert(decision.job_id), 2000));

    return () => timeouts.forEach((timeout) => window.clearTimeout(timeout));
  }, [runId]);

  if (visibleJobIds.length === 0) return null;

  return (
    <div className="floating-alert-stack" aria-live="polite">
      {admittedJobs
        .filter((decision) => visibleJobIds.includes(decision.job_id))
        .map((decision) => (
          <div className={`floating-alert ${closingJobIds.includes(decision.job_id) ? "closing" : ""}`} key={decision.job_id}>
            <div>
              <strong>{decision.job_id} admitted</strong>
              <span>Decision changed from shifted to admitted for this clean window.</span>
            </div>
            <button
              aria-label={`Close alert for ${decision.job_id}`}
              onClick={() => closeAlert(decision.job_id)}
              type="button"
            >
              ×
            </button>
          </div>
        ))}
    </div>
  );
}

export function GridFlexDashboard({ data, dataSource, statusMessage, apiBaseUrl }: DashboardProps) {
  const capacity = useMemo(() => {
    const totalGpuRequested = data.workloads.reduce((sum, workload) => sum + workload.gpu_count, 0);
    const totalEnergy = data.workloads.reduce((sum, workload) => sum + workload.estimated_energy_kwh, 0);
    const peakEstimatedKw = Math.max(
      ...data.workloads.map((workload) => workload.estimated_energy_kwh / Math.max(workload.duration_minutes / 60, 0.5)),
      0
    );
    const averageTariff = average(data.grid_windows.map((window) => window.tariff_p_per_kwh));

    return {
      totalGpuRequested,
      totalEnergy,
      peakEstimatedKw,
      averageTariff
    };
  }, [data]);

  return (
    <main className="shell">
      <AdmissionAlerts decisions={data.decisions} key={data.run_id} runId={data.run_id} />
      <section className="hero">
        <div>
          <p className="eyebrow">GridFlex Compute · NVIDIA Hackathon Demo · {data.scheduler_mode}</p>
          <h1>GridFlex AI Command Center</h1>
          <p className="lede">
            Grid-aware GPU scheduling for AI workloads, using {data.data_basis}. The dashboard combines DGX
            pipeline evidence, live carbon orchestration, and Nemotron-style operator explanations to show when
            jobs should run now versus shift into cleaner grid windows.
          </p>
          <div className="button-row hero-actions">
            <Link className="button primary" href="/dashboard/live-carbon">
              Open Live Carbon Orchestrator
            </Link>
            <Link className="button" href="/dashboard/control-loop">
              Open Control Loop Demo
            </Link>
          </div>
        </div>
        <aside className="meta-card">
          Demo run
          <strong>{data.run_id}</strong>
          <br />
          Generated
          <strong>{new Date(data.generated_at).toLocaleString()}</strong>
          <br />
          Viewed live
          <LiveTimestamp />
          <br />
          Source
          <strong>{dataSource === "api" ? "Live API" : "Mock fallback"}</strong>
          {apiBaseUrl ? (
            <>
              <br />
              Endpoint
              <strong>{apiBaseUrl}</strong>
            </>
          ) : null}
        </aside>
      </section>

      <section className="description-panel">
        <strong>Demo objective</strong>
        <p>
          Prove that GPU jobs can preserve utilisation while reducing grid stress, carbon exposure, and peak energy
          pressure across a London smart-meter derived workload simulation.
        </p>
      </section>

      <section className="capacity-grid" aria-label="GPU capacity and energy parameters">
        <CapacityCard label="GPU demand" value={`${capacity.totalGpuRequested} GPUs`} detail="Requested across queued jobs" />
        <CapacityCard label="Power" value={`${capacity.peakEstimatedKw.toFixed(1)} kW`} detail="Peak estimated workload draw" />
        <CapacityCard label="Storage" value="Ready" detail="LCL cache + mock payload available" />
        <CapacityCard label="Consumption" value={formatKwh(capacity.totalEnergy)} detail="Queued workload energy" />
        <CapacityCard label="Rate" value={`${capacity.averageTariff.toFixed(1)}p/kWh`} detail="Average grid tariff window" />
        <CapacityCard label="Jobs running" value={data.kpis.jobs_admitted_now} detail="Admitted immediately" />
      </section>

      {statusMessage ? (
        <section className="panel" aria-live="polite">
          <strong>{dataSource === "api" ? "Connected to backend" : "Live API unavailable"}</strong>
          <p>{statusMessage}</p>
          <div className="button-row">
            <Link className="button" href="/dashboard/live-carbon">
              Open Live Carbon Orchestrator
            </Link>
            <Link className="button" href="/dashboard/control-loop">
              Open Control Loop Demo
            </Link>
          </div>
        </section>
      ) : null}

      <section className="kpi-grid" aria-label="GridFlex KPIs">
        <KpiCard label="Jobs shifted" value={`${data.kpis.jobs_shifted}/${data.kpis.jobs_total}`} />
        <KpiCard label="Jobs admitted now" value={data.kpis.jobs_admitted_now} />
        <KpiCard label="GPU utilisation preserved" value={formatPct(data.kpis.gpu_utilisation_preserved_pct)} />
        <KpiCard label="Deadline miss rate" value={formatPct(data.kpis.deadline_miss_rate)} />
        <KpiCard label="Peak kWh avoided" value={data.kpis.peak_kwh_avoided} />
        <KpiCard label="Mean stress before" value={data.kpis.mean_grid_stress_before.toFixed(3)} />
        <KpiCard label="Mean stress after" value={data.kpis.mean_grid_stress_after.toFixed(3)} />
        <KpiCard label="Carbon saved" value={`${data.kpis.estimated_carbon_saving_kgco2} kgCO₂`} />
      </section>

      <section className="dashboard-grid">
        <div>
          <GridTimeline windows={data.grid_windows} />
        </div>
        <div>
          <LiveCarbonSignalCard apiBaseUrl={apiBaseUrl} />
        </div>
      </section>

      <WorkloadTable workloads={data.workloads} decisions={data.decisions} />

      <div style={{ height: 18 }} />

      <DecisionTable decisions={data.decisions} />
    </main>
  );
}