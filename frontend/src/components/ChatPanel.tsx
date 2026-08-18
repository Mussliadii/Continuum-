"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { PaperPlaneRight, ShieldCheck } from "@phosphor-icons/react/dist/ssr";
import type { ActiveIncident, ChatMessage } from "@/lib/types";
import { MessageBubble } from "./MessageBubble";
import { SeverityPill } from "./StatusPill";

export function ChatPanel({
  messages,
  incident,
  sending,
  onSend,
  onCitationClick,
  onResolveClick,
}: {
  messages: ChatMessage[];
  incident: ActiveIncident | null;
  sending: boolean;
  onSend: (text: string) => void;
  onCitationClick: (shortId: string) => void;
  onResolveClick: () => void;
}) {
  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  function submitDraft() {
    const text = draft.trim();
    if (!text || sending) return;
    onSend(text);
    setDraft("");
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    submitDraft();
  }

  return (
    <div className="flex-1 min-w-[480px] flex flex-col min-h-0">
      {incident && incident.status !== "resolved" && (
        <div
          className="flex items-center justify-between gap-3 px-4 py-2 border-b"
          style={{ borderColor: "var(--color-status-critical)" }}
        >
          <div className="flex items-center gap-2 min-w-0">
            <SeverityPill severity={incident.severity} />
            <span className="text-sm font-medium truncate">{incident.title}</span>
          </div>
          <button
            type="button"
            onClick={onResolveClick}
            className="shrink-0 inline-flex items-center gap-1.5 text-xs font-medium text-status-healthy hover:opacity-80 cursor-pointer"
          >
            <ShieldCheck size={16} aria-hidden />
            Mark resolved
          </button>
        </div>
      )}

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center gap-2 px-6">
            <div
              className="h-2.5 w-2.5 rounded-full cluster-pulse mb-2"
              style={{ backgroundColor: "var(--color-status-healthy)" }}
              aria-hidden
            />
            <p className="text-sm font-medium">All systems normal</p>
            <p className="text-sm text-muted-foreground max-w-sm">
              Describe what you&apos;re seeing — symptoms, error logs, or a hunch — and
              Continuum will check its memory for anything similar.
            </p>
          </div>
        ) : (
          messages.map((m) => (
            <MessageBubble key={m.id} message={m} onCitationClick={onCitationClick} />
          ))
        )}
      </div>

      <form onSubmit={handleSubmit} className="border-t border-border p-3 flex gap-2 items-end">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submitDraft();
            }
          }}
          placeholder="Describe what you're seeing..."
          rows={1}
          disabled={sending}
          className="flex-1 resize-none rounded-md border border-border bg-surface px-3 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={sending || !draft.trim()}
          aria-label="Send message"
          className="shrink-0 h-11 w-11 flex items-center justify-center rounded-md bg-accent text-white disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer hover:opacity-90 transition-opacity"
        >
          {sending ? (
            <span
              className="h-4 w-4 rounded-full border-2 border-white/40 border-t-white animate-spin"
              aria-hidden
            />
          ) : (
            <PaperPlaneRight size={18} weight="fill" aria-hidden />
          )}
        </button>
      </form>
    </div>
  );
}
