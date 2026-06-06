import { GridFlexDashboard } from "@/components/GridFlexDashboard";
import { getDemoData } from "@/lib/demo-data";

export default async function DashboardPage() {
  const data = await getDemoData();

  return <GridFlexDashboard data={data} />;
}