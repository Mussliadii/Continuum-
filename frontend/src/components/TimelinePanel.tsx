import { ListChecks } from "@phosphor-icons/react/dist/ssr";
import type { IncidentEvent } from "@/lib/types";

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

const EVENT_LABEL: Record<IncidentEvent["event_type"], string> = {
  message: "message",
  hypothesis: "hypothesis",
  action: "action",
  citation: "cited evidence",
};

export function TimelinePanel({ events }: { events: IncidentEvent[] }) {
  const relevant = events.filter((e) => e.event_type !== "message");

  return (
    <section aria-labelledby="timeline-heading" className="p-4">
      <h2
        id="timeline-heading"
        className="text-xs font-semibold tracking-wide text-muted-foreground uppercase mb-3 flex items-center gap-1.5"
      >
        <ListChecks size={14} aria-hidden />
        Incident Timeline
      </h2>

      {relevant.length === 0 && (
        <p className="text-sm text-muted-foreground">
          No active incident — timeline will populate once you start describing one.
        </p>
      )}

      {relevant.length > 0 && (
        <ol className="space-y-3 border-l border-border pl-3 ml-1">
          {[...relevant].reverse().map((event, i) => (
            <li key={i} className="relative">
              <span
                className="absolute -left-[17px] top-1 h-2 w-2 rounded-full bg-accent"
                aria-hidden
              />
              <div className="flex items-baseline gap-2">
                <span className="font-mono text-xs text-muted-foreground">
                  {formatTime(event.created_at)}
                </span>
                <span className="text-xs uppercase tracking-wide text-accent">
                  {EVENT_LABEL[event.event_type]}
                </span>
              </div>
              <p className="text-sm text-foreground mt-0.5">{event.content}</p>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
