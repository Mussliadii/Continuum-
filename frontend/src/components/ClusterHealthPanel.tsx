import { Database } from "@phosphor-icons/react/dist/ssr";
import type { ClusterHealth } from "@/lib/types";
import { HealthPill } from "./StatusPill";

export function ClusterHealthPanel({
  clusterHealth,
  loading,
}: {
  clusterHealth: ClusterHealth | null;
  loading: boolean;
}) {
  const healthy =
    clusterHealth !== null &&
    (clusterHealth.state === "CREATED" || clusterHealth.state === "READY");

  return (
    <section aria-labelledby="cluster-health-heading" className="p-4 border-b border-border">
      <h2
        id="cluster-health-heading"
        className="text-xs font-semibold tracking-wide text-muted-foreground uppercase mb-3 flex items-center gap-1.5"
      >
        <Database size={14} aria-hidden />
        Cluster Health
      </h2>

      {loading && (
        <div className="h-20 rounded-lg bg-surface animate-pulse" aria-hidden />
      )}

      {!loading && !clusterHealth && (
        <p className="text-sm text-muted-foreground">
          Not checked yet this session — ask about the database to fetch live status.
        </p>
      )}

      {!loading && clusterHealth && (
        <div className="rounded-lg border border-border bg-surface p-3 space-y-2 font-mono text-xs">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">{clusterHealth.cluster_name}</span>
            <HealthPill healthy={healthy} label={clusterHealth.state} />
          </div>
          <div className="flex items-center justify-between text-muted-foreground">
            <span>version</span>
            <span className="text-foreground">{clusterHealth.cockroach_version}</span>
          </div>
          <div className="flex items-center justify-between text-muted-foreground">
            <span>region</span>
            <span className="text-foreground">{clusterHealth.regions.join(", ")}</span>
          </div>
          <div className="flex items-center justify-between text-muted-foreground">
            <span>active queries</span>
            <span className="text-foreground tabular-nums">
              {clusterHealth.active_query_count}
            </span>
          </div>
        </div>
      )}
    </section>
  );
}
