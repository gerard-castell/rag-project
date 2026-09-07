"use client";

import { useState } from "react";
import { FileText, Plus } from "lucide-react";
import { useDocuments } from "@/contexts/documents-context";
import { useUploadModal } from "@/contexts/upload-modal-context";
import PageHeader from "@/components/shared/PageHeader";
import DocumentCard from "./DocumentCard";

export default function DocumentsView() {
  const { docs, docsLoading, activeDocId, selectDoc, deleteDoc } = useDocuments();
  const { open: openUpload } = useUploadModal();
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const handleDelete = (docId: string) => {
    setDeleteError(null);
    deleteDoc(docId).catch((err: unknown) => {
      setDeleteError(
        err instanceof Error ? err.message : "Failed to delete document."
      );
    });
  };

  return (
    <>
      <PageHeader
        icon={FileText}
        title="Documents"
        subtitle={
          docs.length > 0
            ? `${docs.length} document${docs.length !== 1 ? "s" : ""} indexed`
            : undefined
        }
        action={
          <button
            onClick={openUpload}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-amber text-white text-sm font-medium shadow-[var(--shadow-card)] hover:bg-amber-dark hover:shadow-[var(--shadow-card-hover)] active:scale-[0.98] transition-all"
          >
            <Plus className="w-4 h-4" />
            Upload PDF
          </button>
        }
      />

      {/* Content */}
      <div className="flex-1 overflow-auto p-8">
        {deleteError && (
          <div className="mb-6 p-4 bg-danger-soft text-danger rounded-lg text-sm">
            {deleteError}
          </div>
        )}

        {docsLoading ? (
          <div
            className="grid grid-cols-[repeat(auto-fill,minmax(180px,1fr))] gap-5"
            aria-busy="true"
            aria-label="Loading documents"
          >
            {Array.from({ length: 6 }).map((_, idx) => (
              <div
                key={idx}
                className="w-[180px] bg-surface rounded-xl border border-rim p-4 animate-pulse"
              >
                <div className="w-full h-24 bg-bg-subtle rounded-lg mb-3" />
                <div className="h-3.5 w-3/4 bg-bg-subtle rounded mb-2" />
                <div className="h-3 w-1/2 bg-bg-subtle rounded" />
              </div>
            ))}
          </div>
        ) : docs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center animate-scale-in">
            <div className="relative mb-6">
              <div className="absolute inset-0 rounded-full border-2 border-dashed border-rim-strong scale-125" />
              <div className="relative w-20 h-20 rounded-full bg-amber-soft flex items-center justify-center">
                <FileText className="w-9 h-9 text-amber-dark" strokeWidth={1.5} />
              </div>
            </div>
            <h2 className="text-lg font-serif font-bold text-ink mb-2">
              No documents yet
            </h2>
            <p className="text-ink-muted mb-6 max-w-xs">
              Upload a PDF to get started with search and grounded chat
            </p>
            <button
              onClick={openUpload}
              className="px-6 py-2.5 rounded-lg bg-amber text-white font-medium shadow-[var(--shadow-card)] hover:bg-amber-dark hover:shadow-[var(--shadow-card-hover)] active:scale-[0.98] transition-all"
            >
              Upload your first PDF
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-[repeat(auto-fill,minmax(180px,1fr))] gap-5">
            {docs.map((doc) => (
              <DocumentCard
                key={doc.doc_id}
                doc={doc}
                active={doc.doc_id === activeDocId}
                onSelect={() => selectDoc(doc.doc_id === activeDocId ? null : doc.doc_id)}
                onDelete={() => handleDelete(doc.doc_id)}
              />
            ))}
          </div>
        )}
      </div>
    </>
  );
}
