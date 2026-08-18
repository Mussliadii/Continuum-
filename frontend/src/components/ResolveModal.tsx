"use client";

import { useState, type FormEvent } from "react";
import { X } from "@phosphor-icons/react/dist/ssr";

export interface ResolveFormData {
  description: string;
  root_cause: string;
  resolution: string;
  tags: string[];
}

export function ResolveModal({
  onCancel,
  onSubmit,
  submitting,
}: {
  onCancel: () => void;
  onSubmit: (data: ResolveFormData) => void;
  submitting: boolean;
}) {
  const [description, setDescription] = useState("");
  const [rootCause, setRootCause] = useState("");
  const [resolution, setResolution] = useState("");
  const [tags, setTags] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onSubmit({
      description,
      root_cause: rootCause,
      resolution,
      tags: tags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean),
    });
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="resolve-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      <div
        className="absolute inset-0 bg-black/60"
        onClick={submitting ? undefined : onCancel}
        aria-hidden
      />
      <form
        onSubmit={handleSubmit}
        className="relative w-full max-w-md rounded-lg border border-border bg-surface-raised p-5 space-y-4"
      >
        <div className="flex items-center justify-between">
          <h2 id="resolve-modal-title" className="text-sm font-semibold">
            Resolve incident
          </h2>
          <button
            type="button"
            onClick={onCancel}
            disabled={submitting}
            aria-label="Cancel"
            className="h-11 w-11 -m-2 flex items-center justify-center text-muted-foreground hover:text-foreground cursor-pointer disabled:cursor-not-allowed"
          >
            <X size={18} aria-hidden />
          </button>
        </div>
        <p className="text-xs text-muted-foreground">
          This summary is embedded and added to the knowledge base, so future
          incidents can be matched against it.
        </p>

        <div className="space-y-1">
          <label htmlFor="description" className="text-xs font-medium text-muted-foreground">
            What happened
          </label>
          <textarea
            id="description"
            required
            rows={2}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full resize-none rounded-md border border-border bg-surface px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
          />
        </div>

        <div className="space-y-1">
          <label htmlFor="root_cause" className="text-xs font-medium text-muted-foreground">
            Root cause
          </label>
          <textarea
            id="root_cause"
            required
            rows={2}
            value={rootCause}
            onChange={(e) => setRootCause(e.target.value)}
            className="w-full resize-none rounded-md border border-border bg-surface px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
          />
        </div>

        <div className="space-y-1">
          <label htmlFor="resolution" className="text-xs font-medium text-muted-foreground">
            Resolution
          </label>
          <textarea
            id="resolution"
            required
            rows={2}
            value={resolution}
            onChange={(e) => setResolution(e.target.value)}
            className="w-full resize-none rounded-md border border-border bg-surface px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
          />
        </div>

        <div className="space-y-1">
          <label htmlFor="tags" className="text-xs font-medium text-muted-foreground">
            Tags (comma-separated)
          </label>
          <input
            id="tags"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="database, latency"
            className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent"
          />
        </div>

        <div className="flex justify-end gap-2 pt-1">
          <button
            type="button"
            onClick={onCancel}
            disabled={submitting}
            className="rounded-md px-3 py-2 text-sm text-muted-foreground hover:text-foreground cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50 cursor-pointer"
          >
            {submitting ? "Resolving…" : "Resolve & save to memory"}
          </button>
        </div>
      </form>
    </div>
  );
}
