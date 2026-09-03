import { Plus } from "lucide-react";
import { Doc } from "./AppShell";
import DocumentCard from "./DocumentCard";
import UploadModal from "./UploadModal";

interface DocumentsViewProps {
  docs: Doc[];
  activeDocId: string | null;
  uploadOpen: boolean;
  onUploadOpen: () => void;
  onUploadClose: () => void;
  onUploadSuccess: () => void;
  onSelectDoc: (docId: string) => void;
  onDeleteDoc: (docId: string) => void;
}

export default function DocumentsView({
  docs,
  activeDocId,
  uploadOpen,
  onUploadOpen,
  onUploadClose,
  onUploadSuccess,
  onSelectDoc,
  onDeleteDoc,
}: DocumentsViewProps) {
  return (
    <>
      {/* Header */}
      <div className="flex items-center justify-between px-8 py-6 border-b border-rim bg-surface">
        <h1 className="text-2xl font-serif font-bold text-ink">Documents</h1>
        <button
          onClick={onUploadOpen}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-amber text-white font-medium hover:bg-amber-dark transition-colors"
        >
          <Plus className="w-5 h-5" />
          Upload PDF
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-8">
        {docs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="text-6xl mb-4">📄</div>
            <h2 className="text-lg font-medium text-ink mb-2">
              No documents yet
            </h2>
            <p className="text-ink-muted mb-6 max-w-xs">
              Upload a PDF to get started with search and chat
            </p>
            <button
              onClick={onUploadOpen}
              className="px-6 py-2 rounded-lg bg-accent text-white font-medium hover:bg-accent-dark transition-colors"
            >
              Upload your first PDF
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-[repeat(auto-fill,minmax(180px,1fr))] gap-4">
            {docs.map((doc) => (
              <DocumentCard
                key={doc.doc_id}
                doc={doc}
                active={doc.doc_id === activeDocId}
                onSelect={() => onSelectDoc(doc.doc_id)}
                onDelete={() => onDeleteDoc(doc.doc_id)}
              />
            ))}
          </div>
        )}
      </div>

      <UploadModal
        open={uploadOpen}
        onClose={onUploadClose}
        onSuccess={onUploadSuccess}
      />
    </>
  );
}
