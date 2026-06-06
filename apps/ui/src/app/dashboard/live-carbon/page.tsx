import { CarbonOrchestrationDashboard } from "@/components/CarbonOrchestrationDashboard";
import { getCarbonOrchestrationDemoData } from "@/lib/gridflex-api";

export default async function LiveCarbonDashboardPage() {
  const result = await getCarbonOrchestrationDemoData();

  return (
    <CarbonOrchestrationDashboard
      data={result.data}
      apiBaseUrl={result.apiBaseUrl}
      error={
        result.source === "api"
          ? null
          : result.error ?? "The live carbon orchestration route is unavailable."
      }
    />
  );
}