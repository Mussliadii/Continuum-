"use client";

import { useState } from "react";
import type { ClusterHealth, IncidentEvent, SimilarIncident } from "@/lib/types";
import { SimilarIncidentsPanel } from "./SimilarIncidentsPanel";
import { ClusterHealthPanel } from "./ClusterHealthPanel";
import { TimelinePanel } from "./TimelinePanel";

type Tab = "similar" | "health" | "timeline";

const TABS: { id: Tab; label: string }[] = [
  { id: "similar", label: "Similar" },
  { id: "health", label: "Health" },
  { id: "timeline", label: "Timeline" },
];

export function RightRail({
  similarIncidents,
  similarLoading,
  clusterHealth,
  healthLoading,
  events,
}: {
  similarIncidents: SimilarIncident[];
  similarLoading: boolean;
  clusterHealth: ClusterHealth | null;
  healthLoading: boolean;
  events: IncidentEvent[];
}) {
  const [tab, setTab] = useState<Tab>("similar");

  return (
    <aside
      aria-label="Incident context"
      className="w-full md:w-[360px] shrink-0 border-t md:border-t-0 md:border-l border-border bg-primary overflow-y-auto"
    >
      {/* Tab switcher: only shown below the md breakpoint (DESIGN.MD §3.5) */}
      <div className="flex md:hidden border-b border-border" role="tablist">
        {TABS.map(({ id, label }) => (
          <button
            key={id}
            role="tab"
            aria-selected={tab === id}
            onClick={() => setTab(id)}
            className={`flex-1 py-2.5 text-sm font-medium cursor-pointer transition-colors ${
              tab === id
                ? "text-accent border-b-2 border-accent"
                : "text-muted-foreground"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className={tab === "similar" ? "block" : "hidden md:block"}>
        <SimilarIncidentsPanel incidents={similarIncidents} loading={similarLoading} />
      </div>
      <div className={tab === "health" ? "block" : "hidden md:block"}>
        <ClusterHealthPanel clusterHealth={clusterHealth} loading={healthLoading} />
      </div>
      <div className={tab === "timeline" ? "block" : "hidden md:block"}>
        <TimelinePanel events={events} />
      </div>
    </aside>
  );
}
