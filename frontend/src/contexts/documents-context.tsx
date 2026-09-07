"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { deleteDocument, listDocuments } from "@/lib/api";
import type { Doc } from "@/types/document";

interface DocumentsContextValue {
  docs: Doc[];
  docsLoading: boolean;
  activeDocId: string | null;
  activeDoc: Doc | null;
  selectDoc: (docId: string | null) => void;
  refreshDocs: () => void;
  refreshDocsSoon: () => void;
  deleteDoc: (docId: string) => Promise<void>;
}

const DocumentsContext = createContext<DocumentsContextValue | null>(null);

const REFRESH_AFTER_INGEST_MS = 3000;

export function DocumentsProvider({ children }: { children: ReactNode }) {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [docsLoading, setDocsLoading] = useState(true);
  const [activeDocId, setActiveDocId] = useState<string | null>(null);

  const refreshDocs = useCallback(() => {
    listDocuments()
      .then((fetched) => setDocs(fetched))
      .catch(() => {
        // Keep the previously loaded list if the backend is unreachable.
      })
      .finally(() => setDocsLoading(false));
  }, []);

  useEffect(() => {
    refreshDocs();
  }, [refreshDocs]);

  const refreshDocsSoon = useCallback(() => {
    // Ingestion runs as a background task, so the new document may not be
    // aggregated from Qdrant yet; refresh now and once more shortly after.
    refreshDocs();
    setTimeout(refreshDocs, REFRESH_AFTER_INGEST_MS);
  }, [refreshDocs]);

  const deleteDoc = useCallback(async (docId: string) => {
    await deleteDocument(docId);
    setDocs((prev) => prev.filter((doc) => doc.doc_id !== docId));
    setActiveDocId((prev) => (prev === docId ? null : prev));
  }, []);

  const activeDoc = useMemo(
    () => docs.find((doc) => doc.doc_id === activeDocId) ?? null,
    [docs, activeDocId]
  );

  const value = useMemo<DocumentsContextValue>(
    () => ({
      docs,
      docsLoading,
      activeDocId,
      activeDoc,
      selectDoc: setActiveDocId,
      refreshDocs,
      refreshDocsSoon,
      deleteDoc,
    }),
    [docs, docsLoading, activeDocId, activeDoc, refreshDocs, refreshDocsSoon, deleteDoc]
  );

  return (
    <DocumentsContext.Provider value={value}>
      {children}
    </DocumentsContext.Provider>
  );
}

export function useDocuments(): DocumentsContextValue {
  const ctx = useContext(DocumentsContext);
  if (!ctx) {
    throw new Error("useDocuments must be used within a DocumentsProvider");
  }
  return ctx;
}
