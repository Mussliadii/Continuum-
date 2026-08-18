export type Severity = "critical" | "warning" | "info";

export interface SimilarIncident {
  short_id: string;
  title: string;
  description: string;
  root_cause: string;
  resolution: string;
  severity: Severity;
  distance: number;
}

export interface ClusterHealth {
  cluster_name: string;
  state: string;
  cockroach_version: string;
  regions: string[];
  active_query_count: number;
  note: string;
}

export interface ChatResponse {
  incident_id: string;
  response: string;
  similar_incidents: SimilarIncident[];
  cluster_health: ClusterHealth | null;
}

export interface IncidentEvent {
  actor: "agent" | "user";
  event_type: "message" | "hypothesis" | "action" | "citation";
  content: string;
  created_at: string;
}

export interface ActiveIncident {
  id: string;
  title: string;
  status: "investigating" | "mitigating" | "resolved";
  severity: Severity;
  opened_at: string;
  closed_at: string | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "agent";
  content: string;
  pending?: boolean;
}
