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

function formatReason(value: string) {
  return value.replaceAll("_", " ").toLowerCase();
}

function StatusTag({ label, tone = "default" }: { label: string; tone?: "default" | "ok" | "warn" | "info" }) {
  return <span className={`status-tag ${tone}`}>{label}</span>;
}

function KpiCard({ label, value, detail }: { label: string; value: string | number; detail?: string }) {
  return (
    <article className="kpi-card kpi-card-primary">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
      {detail ? <div className="kpi-detail">{detail}</div> : null}
    </article>
  );
}

function WorkloadDecisionCards({ workloads }: { workloads: CarbonOrchestrationWorkload[] }) {
  return (
    <section className="panel">
      <div className="section-heading-row">
        <div>
          <p className="section-kicker">decision cards</p>
          <h2>Should each workload run now or wait?</h2>
        </div>
      </div>
      <div className="decision-card-grid">
        {workloads.slice(0, 6).map((workload) => (
          <article className={`decision-card ${workload.decision}`} key={workload.job_id}>
            <div className="decision-card-top">
              <strong>{workload.job_id}</strong>
              <span className={`pill ${workload.decision}`}>{formatWorkloadType(workload.decision)}</span>
            </div>
            <h3>{formatWorkloadType(workload.workload_type)}</h3>
            <p>{workload.operator_message}</p>
            <div className="decision-card-meta">
              <span>{workload.gpu_count} GPUs</span>
              <span>{workload.estimated_energy_kwh} kWh</span>
              <span>{workload.deadline_minutes} min deadline</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function WorkloadDecisionTable({ workloads }: { workloads: CarbonOrchestrationWorkload[] }) {
  return (
    <section className="panel">
      <div className="section-heading-row">
        <div>
          <p className="section-kicker">orchestration queue</p>
          <h2>Workload decision table</h2>
        </div>
      </div>
      <div className="table-wrap">
        <table className="data-table data-table-relaxed">
          <thead>
            <tr>
              <th>Type</th>
              <th>Urgency</th>
              <th>Duration</th>
              <th>Energy</th>
              <th>Decision</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            {workloads.map((workload) => (
              <tr key={workload.job_id}>
                <td>{formatWorkloadType(workload.workload_type)}</td>
                <td>
                  <div className="table-primary">{workload.urgency_class}</div>
                  <div className="table-secondary">{workload.job_id}</div>
                </td>
                <td>{workload.estimated_duration_minutes} min</td>
                <td>{workload.estimated_energy_kwh} kWh</td>
                <td>
                  <span className={`pill ${workload.decision}`}>{formatWorkloadType(workload.decision)}</span>
                </td>
                <td className="table-text-wrap">{formatReason(workload.reason)}</td>
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
      <div className="section-heading-row">
        <div>
          <p className="section-kicker">operator guidance</p>
          <h2>Why the workloads landed here</h2>
        </div>
      </div>
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
            <h1>AI Factory Carbon Window</h1>
            <p className="lede">Live UK carbon intensity translated into real-time AI workload admission guidance.</p>
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
          <h1>Should AI training run now or wait for a cleaner grid window?</h1>
          <p className="lede">NESO carbon intensity plus GridFlex policy for fast operator-facing compute admission decisions.</p>
          <p className="hero-copy">The goal is not just lower carbon. It is to preserve throughput while shifting flexible GPU work into cleaner time windows.</p>
          <div className="status-tag-row">
            <StatusTag label="NESO live signal" tone="ok" />
            <StatusTag label={`Policy ${data.status}`} tone={data.status === "ok" ? "ok" : "warn"} />
            <StatusTag label={formatWorkloadType(liveCarbon.recommendation)} tone="info" />
          </div>
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
            <p className="section-kicker">live recommendation</p>
            <h2>Run window recommendation</h2>
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

        <div className="carbon-hero-visual">
          <div className="carbon-hero-number">
            <span>Current carbon intensity</span>
            <strong>{typeof liveCarbon.current_intensity === "number" ? liveCarbon.current_intensity : "--"}</strong>
            <small>gCO2/kWh</small>
          </div>
          <div className="carbon-hero-recommendation">
            <span>Recommendation</span>
            <div className={`carbon-recommendation-badge ${liveCarbon.recommendation}`}>{formatWorkloadType(liveCarbon.recommendation)}</div>
            <p>{liveCarbon.reason}</p>
          </div>
        </div>

        <div className="voice-ready-box">
          <strong>Operator summary</strong>
          <p className="operator-summary">{data.operator_summary}</p>
        </div>
      </section>

      <section className="kpi-grid" aria-label="Carbon orchestration KPIs">
        <KpiCard label="Current intensity" value={intensityText} detail={`Window ${formatTimeWindow(liveCarbon.from)} - ${formatTimeWindow(liveCarbon.to)}`} />
        <KpiCard label="Jobs run now" value={data.kpis.jobs_run_now} detail={`${data.kpis.jobs_total} total queued`} />
        <KpiCard label="Jobs delayed" value={data.kpis.jobs_delayed} detail={`${data.kpis.estimated_energy_shifted_kwh} kWh shifted`} />
        <KpiCard label="Carbon avoided" value={`${data.kpis.estimated_carbon_avoided_kgco2} kgCO₂`} detail="Estimated orchestration gain" />
      </section>

      <section className="dashboard-grid">
        <div className="stack-column">
          <WorkloadDecisionCards workloads={data.workloads} />
          <WorkloadDecisionTable workloads={data.workloads} />
        </div>
        <div className="stack-column">
          <WorkloadOperatorMessages workloads={data.workloads} />
        </div>
      </section>
    </main>
  );
}