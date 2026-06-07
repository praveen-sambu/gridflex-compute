import Link from "next/link";

type DashboardRoute = "dashboard" | "live-carbon" | "control-loop" | "voice-agent";

type DashboardTopNavProps = {
  activeRoute: DashboardRoute;
};

const routes = [
  { key: "dashboard", label: "Main Dashboard", href: "/dashboard" },
  { key: "live-carbon", label: "Live Carbon", href: "/dashboard/live-carbon" },
  { key: "control-loop", label: "Control Loop", href: "/dashboard/control-loop" },
  { key: "voice-agent", label: "Voice Agent", href: "/dashboard/voice-agent" },
] as const;

export function DashboardTopNav({ activeRoute }: DashboardTopNavProps) {
  return (
    <nav className="page-nav button-row" aria-label="Dashboard navigation">
      {routes.map((route) => (
        <Link key={route.key} className={route.key === activeRoute ? "button primary" : "button"} href={route.href}>
          {route.label}
        </Link>
      ))}
      <Link className="button" href="http://localhost:3003" target="_blank" rel="noreferrer">
        Grafana
      </Link>
    </nav>
  );
}