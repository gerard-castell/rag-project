import { FileText, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { Doc } from "./AppShell";

interface DocumentCardProps {
  doc: Doc;
}

const statusLabel: Record<Doc["status"], string> = {
  processing: "Processing",
  indexed: "Indexed",
  error: "Error",
};

export default function DocumentCard({ doc }: DocumentCardProps) {
  return (
    <div
      className="w-[180px] bg-surface rounded-xl border border-rim hover:shadow-md transition-shadow p-4"
      title={doc.status === "error" ? doc.error : undefined}
    >
      {/* Thumbnail area */}
      <div className="w-full h-20 bg-bg-subtle rounded-lg mb-3 flex items-center justify-center">
        <FileText className="w-8 h-8 text-amber" />
      </div>

      {/* Name */}
      <div className="text-sm font-medium text-ink truncate mb-1" title={doc.name}>
        {doc.name}
      </div>

      {/* Status */}
      <div
        className={`flex items-center gap-1 text-xs mb-1 ${
          doc.status === "error"
            ? "text-danger"
            : doc.status === "indexed"
              ? "text-ink-subtle"
              : "text-amber"
        }`}
      >
        {doc.status === "processing" && (
          <Loader2 className="w-3 h-3 animate-spin" />
        )}
        {doc.status === "indexed" && <CheckCircle2 className="w-3 h-3" />}
        {doc.status === "error" && <AlertCircle className="w-3 h-3" />}
        <span className="truncate">{statusLabel[doc.status]}</span>
      </div>

      {doc.status === "error" && doc.error && (
        <div className="text-xs text-danger truncate mb-1">{doc.error}</div>
      )}

      {/* Date */}
      <div className="text-xs text-ink-subtle">
        {doc.uploadedAt.toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
        })}
      </div>
    </div>
  );
}
