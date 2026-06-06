import Link from "next/link";

import type { CarbonOrchestrationResponse, CarbonOrchestrationWorkload } from "@/types/gridflex";

type CarbonOrchestrationDashboardProps = {
  data: CarbonOrchestrationResponse | null;
  apiBaseUrl?: string | null;
  error?: string | null;
};

const timeFormatter = new Intl.DateTimeFormat("en-GB", {
  hour: "2-digit",
  minute: "2-digit",
  timeZone: "UTC"
});

function formatTimeWindow(value: string | null | undefined) {
  if (!value) {
    return "-";
  }

  return timeFormatter.format(new Date(value));
}

function formatWorkloadType(value: string) {
  return value.replaceAll("_", " ");
}

function KpiCard({ label, value }: { label: string; value: string | number }) {
  return (
    <article className="kpi-card">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
    </article>
  );
}

function WorkloadDecisionTable({ workloads }: { workloads: CarbonOrchestrationWorkload[] }) {
  return (
    <section className="panel">
      <h2>Workload decision table</h2>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Job</th>
              <th>Type</th>
              <th>GPUs</th>
              <th>Duration</th>
              <th>Energy</th>
              <th>Urgency</th>
              <th>Deadline</th>
              <th>Decision</th>
            </tr>
          </thead>
          <tbody>
            {workloads.map((workload) => (
              <tr key={workload.job_id}>
                <td>{workload.job_id}</td>
                <td>{formatWorkloadType(workload.workload_type)}</td>
                <td>{workload.gpu_count}</td>
                <td>{workload.estimated_duration_minutes} min</td>
                <td>{workload.estimated_energy_kwh} kWh</td>
                <td>{workload.urgency_class}</td>
                <td>{workload.deadline_minutes} min</td>
                <td>
                  <span className={`pill ${workload.decision}`}>{formatWorkloadType(workload.decision)}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function WorkloadOperatorMessages({ workloads }: { workloads: CarbonOrchestrationWorkload[] }) {
  return (
    <section className="panel">
      <h2>Operator guidance</h2>
      <div className="insight-list">
        {workloads.map((workload) => (
          <article className="insight" key={workload.job_id}>
            <strong>
              {workload.job_id} · {formatWorkloadType(workload.workload_type)}
            </strong>
            <p>{workload.operator_message}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

export function CarbonOrchestrationDashboard({ data, apiBaseUrl, error }: CarbonOrchestrationDashboardProps) {
  if (!data) {
    return (
      <main className="shell">
        <div className="page-nav button-row">
          <Link className="button" href="/dashboard">
            Back to GridFlex Dashboard
          </Link>
        </div>

        <section className="hero">
          <div>
            <p className="eyebrow">live carbon orchestration</p>
            <h1>AI training admission by live UK carbon intensity</h1>
            <p className="lede">This additive page tells a real-time orchestration story without changing the main DGX-trained GridFlex dashboard.</p>
          </div>
        </section>

        <section className="panel" aria-live="polite">
          <strong>Live carbon orchestrator unavailable</strong>
          <p>{error ?? "The carbon orchestration API route is not currently reachable."}</p>
        </section>
      </main>
    );
  }

  const liveCarbon = data.live_carbon;
  const intensityText = typeof liveCarbon.current_intensity === "number" ? `${liveCarbon.current_intensity} gCO2/kWh` : "Unavailable";

  return (
    <main className="shell">
      <div className="page-nav button-row">
        <Link className="button" href="/dashboard">
          Back to GridFlex Dashboard
        </Link>
      </div>

      <section className="hero">
        <div>
          <p className="eyebrow">live carbon orchestrator</p>
          <h1>Should an AI training workload run now or wait for a cleaner window?</h1>
          <p className="lede">This page combines live NESO carbon intensity with a simple GridFlex orchestration policy to explain real-time admission decisions for GPU workloads.</p>
        </div>
        <aside className="meta-card">
          Source
          <strong>{data.source}</strong>
          <br />
          Status
          <strong>{data.status}</strong>
          <br />
          Endpoint
          <strong>{apiBaseUrl ?? "Unavailable"}</strong>
        </aside>
      </section>

      <section className="panel live-carbon-card" aria-live="polite">
        <div className="live-carbon-header">
          <div>
            <h2>Live carbon recommendation</h2>
            <p className="panel-subtitle">{liveCarbon.reason}</p>
          </div>
          <span className={`pill live-carbon-pill ${liveCarbon.recommendation}`}>{formatWorkloadType(liveCarbon.recommendation)}</span>
        </div>

        <div className="live-carbon-grid">
          <article>
            <span>Current intensity</span>
            <strong>{intensityText}</strong>
          </article>
          <article>
            <span>Carbon index</span>
            <strong>{liveCarbon.index}</strong>
          </article>
          <article>
            <span>Live window</span>
            <strong>
              {formatTimeWindow(liveCarbon.from)} - {formatTimeWindow(liveCarbon.to)}
            </strong>
          </article>
        </div>

        <div className="voice-ready-box">
          <strong>Operator summary</strong>
          <p className="operator-summary">{data.operator_summary}</p>
        </div>
      </section>

      <section className="kpi-grid" aria-label="Carbon orchestration KPIs">
        <KpiCard label="Jobs total" value={data.kpis.jobs_total} />
        <KpiCard label="Jobs run now" value={data.kpis.jobs_run_now} />
        <KpiCard label="Jobs delayed" value={data.kpis.jobs_delayed} />
        <KpiCard label="Energy shifted" value={`${data.kpis.estimated_energy_shifted_kwh} kWh`} />
        <KpiCard label="Carbon avoided" value={`${data.kpis.estimated_carbon_avoided_kgco2} kgCO₂`} />
      </section>

      <section className="dashboard-grid">
        <div>
          <WorkloadDecisionTable workloads={data.workloads} />
        </div>
        <div>
          <WorkloadOperatorMessages workloads={data.workloads} />
        </div>
      </section>
    </main>
  );
}