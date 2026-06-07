import Link from "next/link";

import type { Decision, GridFlexResponse, GridWindow, LiveCarbonSignalResponse, Workload } from "@/types/gridflex";

import { DashboardTopNav } from "@/components/DashboardTopNav";
import { LiveCarbonSignalCard } from "@/components/LiveCarbonSignalCard";

type DashboardProps = {
  data: GridFlexResponse;
  dataSource: "api" | "mock";
  statusMessage?: string | null;
  apiBaseUrl?: string | null;
  liveCarbonSignal?: LiveCarbonSignalResponse | null;
};

const timeFormatter = new Intl.DateTimeFormat("en-GB", {
  hour: "2-digit",
  minute: "2-digit",
  timeZone: "UTC"
});

function formatTime(value: string) {
  return timeFormatter.format(new Date(value));
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

  return `${day}/${month}/${year}, ${hours}:${minutes} UTC`;
}

function formatPct(value: number) {
  return `${value.toFixed(value % 1 === 0 ? 0 : 1)}%`;
}

function formatWorkloadType(value: string) {
  return value.replaceAll("_", " ");
}

function explanationPreview(value: string) {
  const compact = value.split(/\s+/).filter(Boolean).join(" ");
  return compact.length > 110 ? `${compact.slice(0, 107)}...` : compact;
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

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <article className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function StressComparison({
  before,
  after,
  jobsShifted,
  peakKwhAvoided,
  carbonSavingKg,
  deadlineMissRate,
}: {
  before: number;
  after: number;
  jobsShifted: number;
  peakKwhAvoided: number;
  carbonSavingKg: number;
  deadlineMissRate: number;
}) {
  const beforePct = Math.max(10, Math.min(100, before * 100));
  const afterPct = Math.max(8, Math.min(100, after * 100));
  const reductionPct = Math.max(0, ((before - after) / Math.max(before, 0.001)) * 100);

  return (
    <section className="panel stress-comparison-panel">
      <div className="section-heading-row">
        <div>
          <p className="section-kicker">grid stress summary</p>
          <h2>Grid Stress Impact</h2>
        </div>
        <StatusTag label={`${reductionPct.toFixed(1)}% stress reduction`} tone="ok" />
      </div>

      <p className="stress-scale-note">Grid stress is a normalized 0-1 score. Lower is better.</p>

      <div className="stress-compare-grid">
        <div className="stress-meter-card before">
          <span className="stress-meter-label">Average stress before</span>
          <strong>{before.toFixed(3)}</strong>
          <div className="stress-meter-track" aria-label="Before grid stress">
            <div className="stress-danger-line" />
            <div className="stress-meter-fill before" style={{ width: `${beforePct}%` }} />
          </div>
        </div>

        <div className="stress-meter-card after">
          <span className="stress-meter-label">Average stress after</span>
          <strong>{after.toFixed(3)}</strong>
          <div className="stress-meter-track" aria-label="After grid stress">
            <div className="stress-danger-line" />
            <div className="stress-meter-fill after" style={{ width: `${afterPct}%` }} />
          </div>
        </div>
      </div>

      <div className="stress-kpi-row" aria-label="Grid stress supporting KPIs">
        <div className="stress-kpi-chip">
          <span>Jobs shifted</span>
          <strong>{jobsShifted}</strong>
        </div>
        <div className="stress-kpi-chip">
          <span>Peak kWh avoided</span>
          <strong>{peakKwhAvoided.toFixed(2)}</strong>
        </div>
        <div className="stress-kpi-chip">
          <span>Carbon saving</span>
          <strong>{carbonSavingKg.toFixed(2)} kgCO2</strong>
        </div>
        <div className="stress-kpi-chip">
          <span>Deadline miss rate</span>
          <strong>{formatPct(deadlineMissRate)}</strong>
        </div>
      </div>

      <p className="stress-annotation">Average grid stress drops by {reductionPct.toFixed(2)}% while flexible jobs are shifted to reduce pressure on the system.</p>
    </section>
  );
}

function RoutingPipeline({ workloads, decisions }: { workloads: Workload[]; decisions: Decision[] }) {
  const decisionByJob = new Map(decisions.map((decision) => [decision.job_id, decision]));
  const highlighted = workloads.slice(0, 4).map((workload) => ({
    workload,
    decision: decisionByJob.get(workload.job_id),
  }));

  const runNow = highlighted.filter((entry) => entry.decision?.decision !== "shifted");
  const shifted = highlighted.filter((entry) => entry.decision?.decision === "shifted");
  const evaluatingRules = [
    "Grid stress threshold",
    "GPU utilisation preservation",
    "Deadline protection",
    "Carbon-aware shift window",
  ];

  return (
    <section className="panel simulator-panel">
      <div className="section-heading-row">
        <div>
          <p className="section-kicker">routing pipeline</p>
          <h2>Incoming AI jobs are routed through the GridFlex admission plane</h2>
        </div>
        <StatusTag label={`${shifted.length} shifted`} tone={shifted.length > 0 ? "warn" : "ok"} />
      </div>

      <div className="routing-pipeline">
        <div className="routing-column incoming">
          <div className="routing-column-header">
            <span>1. Incoming requests</span>
            <strong>{highlighted.length}</strong>
          </div>
          <p className="routing-lane-caption">High-priority AI requests entering the admission plane right now.</p>
          <div className="routing-card-stack">
            {highlighted.map(({ workload }) => (
              <article className="routing-card incoming featured" key={`incoming-${workload.job_id}`}>
                <strong>{workload.job_id}</strong>
                <span>{formatWorkloadType(workload.workload_type)}</span>
                <small>{workload.gpu_count} GPUs · {workload.urgency_class}</small>
                <div className="routing-card-badge">queued</div>
              </article>
            ))}
          </div>
        </div>

        <div className="routing-engine">
          <div className="routing-arrow" />
          <div className="routing-engine-core pulse-frame">
            <span>2. Two-phase admission kernel</span>
            <strong>Stress, deadlines, carbon, DGX utilisation</strong>
            <p className="routing-kernel-copy">The kernel decides whether to admit immediately or defer into a cleaner, lower-stress operating window.</p>
            <div className="engine-rule-list">
              {evaluatingRules.map((rule) => (
                <div className="engine-rule-pill" key={rule}>{rule}</div>
              ))}
            </div>
          </div>
          <div className="routing-arrow split" />
        </div>

        <div className="routing-results">
          <div className="routing-lane run-now">
            <div className="routing-column-header">
              <span>3A. DGX compute fabric</span>
              <strong>{runNow.length}</strong>
            </div>
            <p className="routing-lane-caption">Workloads admitted for immediate execution on available accelerated capacity.</p>
            <div className="routing-card-stack">
              {runNow.map(({ workload, decision }) => (
                <article className="routing-card run-now featured" key={`run-${workload.job_id}`}>
                  <strong>{workload.job_id}</strong>
                  <span>{formatWorkloadType(workload.workload_type)}</span>
                  <small>{decision ? `${formatTime(decision.scheduled_start)} UTC` : "Ready now"}</small>
                  <div className="routing-card-badge ok">admitted</div>
                </article>
              ))}
            </div>
          </div>

          <div className="routing-lane shifted">
            <div className="routing-column-header">
              <span>3B. Clean energy queue</span>
              <strong>{shifted.length}</strong>
            </div>
            <p className="routing-lane-caption">Flexible jobs delayed to protect the grid and move toward better carbon intensity.</p>
            <div className="routing-card-stack">
              {shifted.map(({ workload, decision }) => (
                <div className="routing-shifted-entry" key={`shift-${workload.job_id}`}>
                  <article className="routing-card shifted featured">
                    <strong>{workload.job_id}</strong>
                    <span>{formatWorkloadType(workload.workload_type)}</span>
                    <small>{decision ? `${decision.delay_minutes} min deferral` : "Deferred"}</small>
                    <div className="routing-card-badge warn">shifted</div>
                  </article>
                  <p className="routing-explanation">{decision ? explanationPreview(decision.nim_explanation) : "Deferred into a lower-stress operating window."}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function NavCard({
  title,
  description,
  href,
  external = false,
}: {
  title: string;
  description: string;
  href: string;
  external?: boolean;
}) {
  const content = (
    <>
      <span className="nav-card-label">Open</span>
      <strong>{title}</strong>
      <p>{description}</p>
    </>
  );

  if (external) {
    return (
      <a className="nav-card" href={href} rel="noreferrer" target="_blank">
        {content}
      </a>
    );
  }

  return (
    <Link className="nav-card" href={href}>
      {content}
    </Link>
  );
}

function GridTimeline({ windows }: { windows: GridWindow[] }) {
  return (
    <section className="panel">
      <div className="section-heading-row">
        <div>
          <p className="section-kicker">grid stress forecast</p>
          <h2>24 half-hour operating windows</h2>
        </div>
        <StatusTag label="DGX payload active" tone="ok" />
      </div>
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
      <div className="section-heading-row">
        <div>
          <p className="section-kicker">operations queue</p>
          <h2>Active workload queue details</h2>
        </div>
      </div>
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Job</th>
              <th>Type</th>
              <th>GPUs</th>
              <th>Urgency</th>
              <th>Decision</th>
              <th>Scheduled</th>
            </tr>
          </thead>
          <tbody>
            {workloads.slice(0, 8).map((workload) => {
              const decision = decisionByJob.get(workload.job_id);

              return (
                <tr key={workload.job_id}>
                  <td>
                    <div className="table-primary">{workload.job_id}</div>
                    <div className="table-secondary">{workload.tenant}</div>
                  </td>
                  <td>{formatWorkloadType(workload.workload_type)}</td>
                  <td>{workload.gpu_count}</td>
                  <td>{workload.urgency_class}</td>
                  <td>
                    <span className={`pill ${decision?.decision ?? "pending"}`}>{formatWorkloadType(decision?.decision ?? "pending")}</span>
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
      <div className="section-heading-row">
        <div>
          <p className="section-kicker">decision ledger</p>
          <h2>Scheduling decisions</h2>
        </div>
      </div>
      <div className="table-wrap">
        <table className="data-table data-table-relaxed">
          <thead>
            <tr>
              <th>Job</th>
              <th>Decision</th>
              <th>Delay</th>
              <th>Energy</th>
              <th>Reason</th>
              <th>Explanation</th>
            </tr>
          </thead>
          <tbody>
            {decisions.slice(0, 8).map((decision) => (
              <tr key={decision.job_id}>
                <td>{decision.job_id}</td>
                <td>
                  <span className={`pill ${decision.decision}`}>{formatWorkloadType(decision.decision)}</span>
                </td>
                <td>{decision.delay_minutes} min</td>
                <td>{decision.estimated_energy_kwh.toFixed(2)} kWh</td>
                <td>
                  <div className="table-primary">{decision.reason_code}</div>
                  <div className="table-secondary">
                    {decision.grid_stress_before.toFixed(3)} to {decision.grid_stress_after.toFixed(3)} stress
                  </div>
                </td>
                <td className="table-text-wrap">{explanationPreview(decision.nim_explanation)}</td>
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
      <div className="section-heading-row">
        <div>
          <p className="section-kicker">operator brief</p>
          <h2>Decision explanations</h2>
        </div>
      </div>
      <div className="insight-list">
        {decisions.slice(0, 4).map((decision) => (
          <article className="insight" key={decision.job_id}>
            <strong>
              {decision.job_id} · {formatWorkloadType(decision.decision)}
            </strong>
            <p>{decision.nim_explanation}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

export function GridFlexDashboard({ data, dataSource, statusMessage, apiBaseUrl, liveCarbonSignal }: DashboardProps) {
  return (
    <main className="shell">
      <DashboardTopNav activeRoute="dashboard" />

      <section className="hero">
        <div>
          <p className="eyebrow">GridFlex Compute v2</p>
          <h1>AI Factory Control Room</h1>
          <p className="lede">Grid-aware AI workload orchestration for urban compute.</p>
          <p className="hero-copy">DGX-trained workload scheduling with grid-stress and carbon-aware decisions, presented as an operator-facing control-room view.</p>
          <div className="status-tag-row">
            <StatusTag label={dataSource === "api" ? "Live API" : "Mock fallback"} tone={dataSource === "api" ? "ok" : "warn"} />
            <StatusTag label="DGX payload active" tone="ok" />
            <StatusTag label="Prometheus metrics" tone="info" />
            <StatusTag label="Live carbon active" tone="ok" />
          </div>
        </div>
        <aside className="meta-card">
          Operations snapshot
          <strong>{data.run_id}</strong>
          <br />
          Generated
          <strong>{formatUtcDateTime(data.generated_at)}</strong>
          <br />
          Scheduler mode
          <strong>{data.scheduler_mode}</strong>
          <br />
          Payload basis
          <strong>{data.model_mode}</strong>
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
          <div className="section-heading-row">
            <div>
              <p className="section-kicker">system status</p>
              <h2>{dataSource === "api" ? "Connected to backend" : "Live API unavailable"}</h2>
            </div>
            <StatusTag label={dataSource === "api" ? "Control room live" : "Fallback-safe"} tone={dataSource === "api" ? "ok" : "warn"} />
          </div>
          <p className="panel-subtitle">{statusMessage}</p>
          <div className="nav-card-grid">
            <NavCard title="Live Carbon Orchestrator" description="Should AI training run now or wait for a cleaner grid window?" href="/dashboard/live-carbon" />
            <NavCard title="Live Control Loop" description="Real-time AI factory control loop with bounded DGX pulse controls." href="/dashboard/control-loop" />
            <NavCard title="Voice Memory Agent" description="ElevenLabs plus NVIDIA Nemotron voice-memory demo route." href="/dashboard/voice-agent" />
            <NavCard title="Grafana Observability" description="Operations overview for metrics, payload health, and shift efficiency." href="http://localhost:3003" external />
          </div>
        </section>
      ) : null}

      <section className="kpi-grid kpi-grid-primary" aria-label="GridFlex KPIs">
        <KpiCard label="Jobs total" value={data.kpis.jobs_total} detail={`${data.kpis.jobs_shifted} shifted by policy`} />
        <KpiCard label="Jobs shifted" value={data.kpis.jobs_shifted} detail={`${data.kpis.jobs_admitted_now} admitted now`} />
        <KpiCard label="Peak kWh avoided" value={data.kpis.peak_kwh_avoided.toFixed(2)} detail="Peak shaving from deferred AI loads" />
        <KpiCard label="Carbon saving" value={`${data.kpis.estimated_carbon_saving_kgco2.toFixed(2)} kgCO₂`} detail="Estimated scheduling gain" />
      </section>

      <section className="metric-strip" aria-label="GridFlex secondary metrics">
        <MetricCard label="GPU utilisation preserved" value={formatPct(data.kpis.gpu_utilisation_preserved_pct)} />
        <MetricCard label="Grid stress before" value={data.kpis.mean_grid_stress_before.toFixed(3)} />
        <MetricCard label="Grid stress after" value={data.kpis.mean_grid_stress_after.toFixed(3)} />
        <MetricCard label="Deadline miss rate" value={formatPct(data.kpis.deadline_miss_rate)} />
      </section>

      <section className="dashboard-grid">
        <div className="stack-column">
          <StressComparison
            before={data.kpis.mean_grid_stress_before}
            after={data.kpis.mean_grid_stress_after}
            jobsShifted={data.kpis.jobs_shifted}
            peakKwhAvoided={data.kpis.peak_kwh_avoided}
            carbonSavingKg={data.kpis.estimated_carbon_saving_kgco2}
            deadlineMissRate={data.kpis.deadline_miss_rate}
          />
          <RoutingPipeline workloads={data.workloads} decisions={data.decisions} />
          <GridTimeline windows={data.grid_windows} />
          <WorkloadTable workloads={data.workloads} decisions={data.decisions} />
          <DecisionTable decisions={data.decisions} />
        </div>
        <div className="stack-column">
          <LiveCarbonSignalCard apiBaseUrl={apiBaseUrl} disableLiveFetch initialSignal={liveCarbonSignal} />
          <DecisionInsights decisions={data.decisions} />
        </div>
      </section>
    </main>
  );
}