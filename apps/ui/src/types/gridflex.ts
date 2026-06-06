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

export type LiveCarbonSignalResponse = {
  status: "ok" | "fallback";
  source: string;
  current_intensity: number | null;
  index: string;
  from?: string | null;
  to?: string | null;
  recommendation: "run_now" | "run_selective" | "delay_flexible_jobs" | "use_gridflex_forecast" | string;
  reason: string;
  operator_message: string;
};

export type CarbonOrchestrationKpis = {
  jobs_total: number;
  jobs_run_now: number;
  jobs_delayed: number;
  estimated_energy_shifted_kwh: number;
  estimated_carbon_avoided_kgco2: number;
};

export type CarbonOrchestrationWorkload = {
  job_id: string;
  workload_type: string;
  gpu_count: number;
  estimated_duration_minutes: number;
  estimated_energy_kwh: number;
  urgency_class: string;
  deadline_minutes: number;
  decision: string;
  reason: string;
  operator_message: string;
};

export type CarbonOrchestrationResponse = {
  status: "ok" | "fallback";
  source: string;
  live_carbon: LiveCarbonSignalResponse;
  kpis: CarbonOrchestrationKpis;
  workloads: CarbonOrchestrationWorkload[];
  operator_summary: string;
};

export type DemoReadinessResponse = {
  dgx_backend_ready: boolean;
  demo_payload_ready: boolean;
  live_carbon_ready: boolean;
  coordination_api_ready_public: boolean;
  nim_configured: boolean;
  gpu_pulse_enabled: boolean;
  metrics_ready: boolean;
  dgx_payload_used?: boolean;
};

export type GpuPulseCapabilities = {
  gpu_pulse_enabled: boolean;
  nvidia_smi_available: boolean;
  nvcc_available: boolean;
  numpy_available: boolean;
};

export type ControlLoopSourceFlags = {
  live_carbon_used: boolean;
  coordination_api_used: boolean;
  coordination_api_fallback: boolean;
  nemotron_used: boolean;
  nemotron_fallback: boolean;
  dgx_payload_used: boolean;
};

export type ControlLoopComponentSources = {
  live_carbon: string;
  coordination_api: string;
  nemotron: string;
  dgx_payload: string;
  gpu_pulse: GpuPulseCapabilities;
};

export type ControlLoopIncomingJob = {
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

export type ControlLoopDemoResponse = {
  status: string;
  active_payload: string;
  live_carbon_signal: LiveCarbonSignalResponse;
  sample_incoming_ai_training_job: ControlLoopIncomingJob;
  decision: string;
  reason: string;
  estimated_energy_shifted_kwh: number;
  operator_message: string;
  source_fields: ControlLoopSourceFlags;
  sources: ControlLoopSourceFlags;
  component_sources: ControlLoopComponentSources;
  readiness: DemoReadinessResponse;
};

export type GpuPulseDemoResponse = {
  status: "ok" | "disabled";
  message?: string;
  started_at?: string;
  duration_ms?: number;
  backend_used?: string;
  safe_limit_seconds?: number;
  nvidia_smi_before?: string | null;
  nvidia_smi_after?: string | null;
  details?: {
    iterations: number;
    checksum: number;
    target_runtime_seconds: number;
  };
};

export type VoiceAgentEvent = {
  timestamp: string;
  session_id: string;
  event_type: string;
  payload: Record<string, unknown>;
};

export type VoiceAgentStatusResponse = {
  status: string;
  session_id: string;
  started_at: string;
  uptime_minutes: number;
  target_minutes: number;
  events_logged: number;
  nemotron_configured: boolean;
  elevenlabs_configured: boolean;
  session_logging_active: boolean;
};

export type VoiceAgentSessionResponse = {
  session_id: string;
  events: VoiceAgentEvent[];
  events_logged: number;
};

export type VoiceAgentEvidenceResponse = {
  session_started_at: string;
  current_time: string;
  uptime_minutes: number;
  target_minutes: number;
  target_met: boolean;
  events_logged: number;
  log_file: string;
};

export type VoiceAgentMessageResponse = {
  source: "nvidia-nemotron" | "fallback" | string;
  reply: string;
  memory_used: boolean;
  events_logged: number;
  audio_available: boolean;
  audio_url: string | null;
  fallback_reason?: string | null;
};