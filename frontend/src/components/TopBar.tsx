import { Hexagon } from "@phosphor-icons/react/dist/ssr";
import type { ActiveIncident, ClusterHealth } from "@/lib/types";
import { SeverityPill, HealthPill } from "./StatusPill";

export function TopBar({
  incident,
  clusterHealth,
}: {
  incident: ActiveIncident | null;
  clusterHealth: ClusterHealth | null;
}) {
  const healthy =
    clusterHealth === null ||
    clusterHealth.state === "CREATED" ||
    clusterHealth.state === "READY";

  return (
    <header className="h-14 shrink-0 flex items-center justify-between px-4 border-b border-border bg-primary">
      <div className="flex items-center gap-3 min-w-0">
        <Hexagon size={22} weight="bold" className="text-accent shrink-0" aria-hidden />
        <span className="font-mono font-semibold text-sm tracking-wide shrink-0">
          CONTINUUM
        </span>
        {incident && (
          <div className="flex items-center gap-2 min-w-0 border-l border-border pl-3 ml-1">
            <SeverityPill severity={incident.severity} />
            <span className="text-sm text-muted-foreground truncate">
              {incident.title}
            </span>
          </div>
        )}
      </div>

      <HealthPill
        healthy={healthy}
        label={
          clusterHealth
            ? `Cluster: ${clusterHealth.state === "CREATED" || clusterHealth.state === "READY" ? "Healthy" : clusterHealth.state}`
            : "Cluster: checking…"
        }
      />
    </header>
  );
}
