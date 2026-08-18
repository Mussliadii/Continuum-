import type { ActiveIncident, ChatResponse, IncidentEvent } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

if (!API_BASE_URL && typeof window !== "undefined") {
  console.error(
    "NEXT_PUBLIC_API_BASE_URL is not set — see frontend/.env.local.example"
  );
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `Request failed with status ${res.status}`);
  }
  return res.json();
}

export function sendChatMessage(
  message: string,
  incidentId: string | null
): Promise<ChatResponse> {
  return request<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify({ message, incident_id: incidentId }),
  });
}

export function getIncident(
  incidentId: string
): Promise<{ incident: ActiveIncident; events: IncidentEvent[] }> {
  return request(`/incidents/${incidentId}`);
}

export function resolveIncident(
  incidentId: string,
  data: {
    description: string;
    root_cause: string;
    resolution: string;
    tags: string[];
  }
): Promise<{ status: string }> {
  return request(`/incidents/${incidentId}/resolve`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}
