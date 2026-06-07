import { GridFlexDashboard } from "@/components/GridFlexDashboard";
import { getDemoData } from "@/lib/demo-data";
import { getLiveCarbonSignalData } from "@/lib/gridflex-api";

export default async function DashboardPage() {
  const result = await getDemoData();
  const liveCarbonSignal = await getLiveCarbonSignalData(result.apiBaseUrl);

  return (
    <GridFlexDashboard
      data={result.data}
      dataSource={result.source}
      apiBaseUrl={result.apiBaseUrl}
      liveCarbonSignal={liveCarbonSignal}
      statusMessage={
        result.source === "api"
          ? `Using ${result.apiBaseUrl}/api/v1/demo for dashboard data.`
          : result.error
            ? `Using the bundled mock payload because the API request failed: ${result.error}`
            : "Using the bundled mock payload."
      }
    />
  );
}