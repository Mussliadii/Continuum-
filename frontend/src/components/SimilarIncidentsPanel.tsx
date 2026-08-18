import { MagnifyingGlass } from "@phosphor-icons/react/dist/ssr";
import type { SimilarIncident } from "@/lib/types";
import { SeverityPill } from "./StatusPill";

function similarityPercent(distance: number): number {
  // Cosine distance is in [0, 2]; map to an intuitive 0-100% match score.
  return Math.round(Math.max(0, 1 - distance / 2) * 100);
}

export function SimilarIncidentsPanel({
  incidents,
  loading,
}: {
  incidents: SimilarIncident[];
  loading: boolean;
}) {
  return (
    <section aria-labelledby="similar-incidents-heading" className="p-4 border-b border-border">
      <h2
        id="similar-incidents-heading"
        className="text-xs font-semibold tracking-wide text-muted-foreground uppercase mb-3"
      >
        Similar Past Incidents
      </h2>

      {loading && (
        <div className="space-y-2" aria-hidden>
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-16 rounded-lg bg-surface animate-pulse" />
          ))}
        </div>
      )}

      {!loading && incidents.length === 0 && (
        <p className="text-sm text-muted-foreground flex items-start gap-2">
          <MagnifyingGlass size={16} className="shrink-0 mt-0.5" aria-hidden />
          No similar incidents yet — this may be a new pattern.
        </p>
      )}

      {!loading && incidents.length > 0 && (
        <ul className="space-y-2">
          {incidents.map((inc) => (
            <li key={inc.short_id}>
              <div
                id={`incident-card-${inc.short_id}`}
                className="rounded-lg border border-border bg-surface p-3 transition-colors hover:bg-surface-raised scroll-mt-4 outline-none focus:ring-2 focus:ring-accent"
                tabIndex={-1}
              >
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span className="font-mono text-xs text-muted-foreground">
                    INC-{inc.short_id}
                  </span>
                  <span className="font-mono text-xs font-medium text-accent">
                    {similarityPercent(inc.distance)}% match
                  </span>
                </div>
                <p className="text-sm font-medium mb-1">{inc.title}</p>
                <div className="flex items-center gap-2 mb-1">
                  <SeverityPill severity={inc.severity} />
                </div>
                <p className="text-xs text-muted-foreground line-clamp-2">
                  {inc.root_cause}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
