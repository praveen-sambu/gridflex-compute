export type StressBand = "low" | "medium" | "high" | string;

export type GridFlexKpis = {
  jobs_total: number;
  jobs_shifted: number;
  jobs_admitted_now: number;
  deadline_miss_rate: number;
  gpu_utilisation_preserved_pct: number;
  peak_kwh_avoided: number;
  mean_grid_stress_before: number;
  mean_grid_stress_after: number;
  estimated_carbon_saving_kgco2: number;
};

export type GridWindow = {
  timestamp: string;
  zone: string;
  grid_stress_score: number;
  predicted_grid_stress_score: number;
  stress_band: StressBand;
  predicted_stress_band: StressBand;
  carbon_intensity_gco2_kwh: number;
  tariff_p_per_kwh: number;
  flexibility_event: boolean;
  source: string;
};

export type Workload = {
  job_id: string;
  tenant: string;
  workload_type: string;
  submitted_at: string;
  duration_minutes: number;
  gpu_count: number;
  estimated_energy_kwh: number;
  urgency_class: string;
  deadline_at: string;
};

export type Decision = {
  job_id: string;
  decision: string;
  original_start: string;
  scheduled_start: string;
  delay_minutes: number;
  grid_stress_before: number;
  grid_stress_after: number;
  estimated_energy_kwh: number;
  estimated_peak_kwh_avoided: number;
  reason_code: string;
  nim_explanation: string;
};

export type GridFlexResponse = {
  run_id: string;
  generated_at: string;
  model_mode: string;
  scheduler_mode: string;
  data_basis: string;
  kpis: GridFlexKpis;
  grid_windows: GridWindow[];
  workloads: Workload[];
  decisions: Decision[];
};