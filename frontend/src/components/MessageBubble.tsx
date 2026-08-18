import type { ReactNode } from "react";
import type { ChatMessage } from "@/lib/types";

const CITATION_PATTERN = /\[INC-([a-f0-9]+)\]/g;

/** Renders agent text, turning `[INC-xxxxxxxx]` citations into clickable
 * chips that scroll the right rail to the matching similarity card —
 * ties the agent's reasoning directly to retrieved evidence instead of
 * reading as an opaque black box. See DESIGN.MD §3.3. */
function renderWithCitations(text: string, onCitationClick: (shortId: string) => void) {
  const parts: ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let key = 0;

  CITATION_PATTERN.lastIndex = 0;
  while ((match = CITATION_PATTERN.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    const shortId = match[1];
    parts.push(
      <button
        key={`citation-${key++}`}
        type="button"
        onClick={() => onCitationClick(shortId)}
        className="inline-flex items-center rounded px-1.5 py-0.5 mx-0.5 text-xs font-mono font-medium border border-accent text-accent hover:bg-accent/10 cursor-pointer transition-colors"
      >
        INC-{shortId}
      </button>
    );
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }
  return parts;
}

export function MessageBubble({
  message,
  onCitationClick,
}: {
  message: ChatMessage;
  onCitationClick: (shortId: string) => void;
}) {
  const isAgent = message.role === "agent";
  return (
    <div className={`flex ${isAgent ? "justify-start" : "justify-end"}`}>
      <div
        className={`max-w-[75ch] rounded-lg px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
          isAgent
            ? "bg-surface border border-border text-foreground"
            : "bg-accent text-accent-foreground"
        } ${message.pending ? "opacity-70" : ""}`}
      >
        {isAgent ? renderWithCitations(message.content, onCitationClick) : message.content}
      </div>
    </div>
  );
}
