import Link from "next/link";

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

function KpiCard({ label, value }: { label: string; value: string | number }) {
  return (
    <article className="kpi-card">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
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
                <tr key={workload.job_id}>
                  <td>{workload.job_id}</td>
                  <td>{workload.tenant}</td>
                  <td>{workload.workload_type.replaceAll("_", " ")}</td>
                  <td>{workload.gpu_count}</td>
                  <td>
                    <span className={`pill ${decision?.decision ?? ""}`}>{decision?.decision ?? "pending"}</span>
                  </td>
                  <td>{decision ? formatTime(decision.scheduled_start) : "—"}</td>
                </tr>
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
                  <span className={`pill ${decision.decision}`}>{decision.decision}</span>
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

function DecisionInsights({ decisions }: { decisions: Decision[] }) {
  return (
    <section className="panel">
      <h2>Decision explanations</h2>
      <div className="insight-list">
        {decisions.slice(0, 4).map((decision) => (
          <article className="insight" key={decision.job_id}>
            <strong>
              {decision.job_id} · {decision.delay_minutes} min delay
            </strong>
            <p>{decision.nim_explanation}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

export function GridFlexDashboard({ data, dataSource, statusMessage, apiBaseUrl }: DashboardProps) {
  return (
    <main className="shell">
      <section className="hero">
        <div>
          <p className="eyebrow">{data.scheduler_mode}</p>
          <h1>Grid-aware GPU workload scheduler</h1>
          <p className="lede">{data.data_basis}</p>
        </div>
        <aside className="meta-card">
          Demo run
          <strong>{data.run_id}</strong>
          <br />
          Generated
          <strong>{new Date(data.generated_at).toLocaleString()}</strong>
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
          <div style={{ height: 18 }} />
          <WorkloadTable workloads={data.workloads} decisions={data.decisions} />
          <div style={{ height: 18 }} />
          <DecisionTable decisions={data.decisions} />
        </div>
        <div>
          <LiveCarbonSignalCard apiBaseUrl={apiBaseUrl} />
          <div style={{ height: 18 }} />
          <DecisionInsights decisions={data.decisions} />
        </div>
      </section>
    </main>
  );
}