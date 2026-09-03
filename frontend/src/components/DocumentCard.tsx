import { FileText, X } from "lucide-react";
import { Doc } from "./AppShell";

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
      className={`group relative w-[180px] bg-surface rounded-xl border p-4 text-left transition-shadow cursor-pointer ${
        active
          ? "border-amber shadow-md"
          : "border-rim hover:shadow-md"
      }`}
    >
      <button
        onClick={(e) => {
          e.stopPropagation();
          onDelete();
        }}
        title="Delete document"
        className="absolute top-2 right-2 p-1 rounded bg-surface border border-rim opacity-0 group-hover:opacity-100 hover:bg-danger-soft hover:text-danger transition-opacity"
      >
        <X className="w-3.5 h-3.5" />
      </button>

      {/* Thumbnail area */}
      <div className="w-full h-20 bg-bg-subtle rounded-lg mb-3 flex items-center justify-center">
        <FileText className="w-8 h-8 text-amber" />
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
