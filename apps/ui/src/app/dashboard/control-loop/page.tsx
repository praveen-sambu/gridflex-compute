import { ControlLoopDashboard } from "@/components/ControlLoopDashboard";
import { getControlLoopDashboardData } from "@/lib/gridflex-api";

export default async function ControlLoopDashboardPage() {
  const result = await getControlLoopDashboardData();

  return (
    <ControlLoopDashboard
      controlLoop={result.controlLoop}
      readiness={result.readiness}
      apiBaseUrl={result.apiBaseUrl}
      error={result.source === "api" ? null : result.error ?? "The control-loop API routes are unavailable."}
    />
  );
}