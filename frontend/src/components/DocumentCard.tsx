import { FileText } from "lucide-react";
import { Doc } from "./AppShell";

interface DocumentCardProps {
  doc: Doc;
}

export default function DocumentCard({ doc }: DocumentCardProps) {
  return (
    <div className="w-[180px] bg-surface rounded-xl border border-rim hover:shadow-md transition-shadow p-4">
      {/* Thumbnail area */}
      <div className="w-full h-20 bg-bg-subtle rounded-lg mb-3 flex items-center justify-center">
        <FileText className="w-8 h-8 text-amber" />
      </div>

      {/* Name */}
      <div className="text-sm font-medium text-ink truncate mb-1" title={doc.name}>
        {doc.name}
      </div>

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
