import { VoiceAgentDashboard } from "@/components/VoiceAgentDashboard";
import { getVoiceAgentDashboardData } from "@/lib/gridflex-api";

export default async function VoiceAgentDashboardPage() {
  const result = await getVoiceAgentDashboardData();

  return (
    <VoiceAgentDashboard
      status={result.status}
      session={result.session}
      evidence={result.evidence}
      apiBaseUrl={result.apiBaseUrl}
      error={result.source === "api" ? null : result.error ?? "The voice-agent routes are unavailable."}
    />
  );
}