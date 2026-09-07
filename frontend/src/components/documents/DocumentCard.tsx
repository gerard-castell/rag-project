import { FileText, X } from "lucide-react";
import type { Doc } from "@/types/document";

interface DocumentCardProps {
  doc: Doc;
  active: boolean;
  onSelect: () => void;
  onDelete: () => void;
}

export default function DocumentCard({
  doc,
  active,
  onSelect,
  onDelete,
}: DocumentCardProps) {
  const uploadedAt = new Date(doc.ingested_at);

  return (
    <div
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") onSelect();
      }}
      className={`group relative w-[180px] bg-surface rounded-xl border p-4 text-left cursor-pointer transition-all duration-200 hover:-translate-y-0.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber ${
        active
          ? "border-amber shadow-[var(--shadow-card-hover)]"
          : "border-rim shadow-[var(--shadow-card)] hover:shadow-[var(--shadow-card-hover)]"
      }`}
    >
      <button
        onClick={(e) => {
          e.stopPropagation();
          onDelete();
        }}
        title="Delete document"
        aria-label={`Delete ${doc.source}`}
        className="absolute top-2 right-2 z-10 p-1 rounded bg-surface border border-rim opacity-0 group-hover:opacity-100 focus:opacity-100 hover:bg-danger-soft hover:text-danger focus:outline-none focus-visible:ring-2 focus-visible:ring-amber transition-opacity"
      >
        <X className="w-3.5 h-3.5" />
      </button>

      {/* Thumbnail: a stylized page mockup rather than a bare icon */}
      <div className="relative w-full h-24 bg-bg-subtle rounded-lg mb-3 overflow-hidden">
        <div className="absolute inset-x-3 top-3 bottom-3 rounded-sm bg-surface border border-rim shadow-sm">
          <div className="flex items-center gap-1 px-2 pt-2">
            <FileText className="w-3 h-3 text-amber flex-shrink-0" />
            <div className="h-1 flex-1 max-w-8 rounded-full bg-amber-soft" />
          </div>
          <div className="px-2 pt-2 space-y-1">
            <div className="h-0.5 w-full rounded-full bg-rim" />
            <div className="h-0.5 w-5/6 rounded-full bg-rim" />
            <div className="h-0.5 w-full rounded-full bg-rim" />
            <div className="h-0.5 w-2/3 rounded-full bg-rim" />
          </div>
        </div>
      </div>

      {/* Name */}
      <div className="text-sm font-medium text-ink truncate mb-1" title={doc.source}>
        {doc.source}
      </div>

      {/* Meta */}
      <div className="text-xs text-ink-subtle">
        {Number.isNaN(uploadedAt.getTime())
          ? ""
          : uploadedAt.toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
            })}
        {doc.page_count > 0 ? ` · ${doc.page_count}p` : ""}
      </div>
    </div>
  );
}
