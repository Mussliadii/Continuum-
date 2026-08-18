"use client";

import { useState } from "react";
import { TopBar } from "@/components/TopBar";
import { LeftRail } from "@/components/LeftRail";
import { ChatPanel } from "@/components/ChatPanel";
import { RightRail } from "@/components/RightRail";
import { ResolveModal, type ResolveFormData } from "@/components/ResolveModal";
import { sendChatMessage, resolveIncident } from "@/lib/api";
import type {
  ActiveIncident,
  ChatMessage,
  ClusterHealth,
  IncidentEvent,
  SimilarIncident,
} from "@/lib/types";

let nextMessageId = 0;

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [incident, setIncident] = useState<ActiveIncident | null>(null);
  const [events, setEvents] = useState<IncidentEvent[]>([]);
  const [similarIncidents, setSimilarIncidents] = useState<SimilarIncident[]>([]);
  const [clusterHealth, setClusterHealth] = useState<ClusterHealth | null>(null);
  const [sending, setSending] = useState(false);
  const [similarLoading, setSimilarLoading] = useState(false);
  const [healthLoading, setHealthLoading] = useState(false);
  const [showResolveModal, setShowResolveModal] = useState(false);
  const [resolving, setResolving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSend(text: string) {
    const userMessage: ChatMessage = { id: `${nextMessageId++}`, role: "user", content: text };
    setMessages((prev) => [...prev, userMessage]);
    setSending(true);
    setSimilarLoading(true);
    setHealthLoading(true);
    setError(null);

    try {
      const result = await sendChatMessage(text, incident?.id ?? null);
      setMessages((prev) => [
        ...prev,
        { id: `${nextMessageId++}`, role: "agent", content: result.response },
      ]);
      setSimilarIncidents(result.similar_incidents);
      if (result.cluster_health) setClusterHealth(result.cluster_health);
      setIncident((prev) =>
        prev ?? {
          id: result.incident_id,
          title: text.slice(0, 80),
          status: "investigating",
          severity: "warning",
          opened_at: new Date().toISOString(),
          closed_at: null,
        }
      );
      setEvents((prev) => [
        ...prev,
        { actor: "user", event_type: "message", content: text, created_at: new Date().toISOString() },
        {
          actor: "agent",
          event_type: "message",
          content: result.response,
          created_at: new Date().toISOString(),
        },
        ...result.similar_incidents.map((hit) => ({
          actor: "agent" as const,
          event_type: "citation" as const,
          content: `[INC-${hit.short_id}] ${hit.title} (distance=${hit.distance.toFixed(3)})`,
          created_at: new Date().toISOString(),
        })),
      ]);
    } catch {
      setError("Couldn't reach Continuum's backend. Check the API is deployed and reachable.");
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setSending(false);
      setSimilarLoading(false);
      setHealthLoading(false);
    }
  }

  function handleCitationClick(shortId: string) {
    const el = document.getElementById(`incident-card-${shortId}`);
    el?.scrollIntoView({ behavior: "smooth", block: "center" });
    el?.focus();
  }

  async function handleResolveSubmit(data: ResolveFormData) {
    if (!incident) return;
    setResolving(true);
    try {
      await resolveIncident(incident.id, data);
      setIncident((prev) => (prev ? { ...prev, status: "resolved" } : prev));
      setShowResolveModal(false);
    } catch {
      setError("Couldn't resolve the incident. Try again.");
    } finally {
      setResolving(false);
    }
  }

  return (
    <div className="flex flex-col h-dvh min-h-dvh">
      <TopBar incident={incident} clusterHealth={clusterHealth} />
      <div className="flex flex-1 min-h-0 flex-col md:flex-row">
        <LeftRail />
        <ChatPanel
          messages={messages}
          incident={incident}
          sending={sending}
          onSend={handleSend}
          onCitationClick={handleCitationClick}
          onResolveClick={() => setShowResolveModal(true)}
        />
        <RightRail
          similarIncidents={similarIncidents}
          similarLoading={similarLoading}
          clusterHealth={clusterHealth}
          healthLoading={healthLoading}
          events={events}
        />
      </div>

      {error && (
        <div
          role="alert"
          className="fixed bottom-4 left-1/2 -translate-x-1/2 rounded-md bg-status-critical px-4 py-2 text-sm text-white shadow-lg"
        >
          {error}
        </div>
      )}

      {showResolveModal && (
        <ResolveModal
          onCancel={() => setShowResolveModal(false)}
          onSubmit={handleResolveSubmit}
          submitting={resolving}
        />
      )}
    </div>
  );
}
