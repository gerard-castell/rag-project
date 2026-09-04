"use client";

import { useCallback, useEffect, useState } from "react";
import { deleteDocument, health, listDocuments, type Doc } from "@/lib/api";
import Sidebar from "./Sidebar";
import DocumentsView from "./DocumentsView";
import SearchView from "./SearchPanel";
import ChatView from "./ChatPanel";

export type { Doc };

type ActiveView = "documents" | "search" | "chat";

const HEALTH_POLL_MS = 15000;

export default function AppShell() {
  const [activeView, setActiveView] = useState<ActiveView>("documents");
  const [docs, setDocs] = useState<Doc[]>([]);
  const [docsLoading, setDocsLoading] = useState(true);
  const [activeDocId, setActiveDocId] = useState<string | null>(null);
  const [collapsed, setCollapsed] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [healthOk, setHealthOk] = useState(false);

  const refreshDocs = useCallback(() => {
    listDocuments()
      .then((fetched) => setDocs(fetched))
      .catch(() => {
        // Keep the previously loaded list if the backend is unreachable.
      })
      .finally(() => setDocsLoading(false));
  }, []);

  useEffect(() => {
    const checkHealth = () => {
      health()
        .then(() => setHealthOk(true))
        .catch(() => setHealthOk(false));
    };
    checkHealth();
    const interval = setInterval(checkHealth, HEALTH_POLL_MS);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    refreshDocs();
  }, [refreshDocs]);

  const handleUploadSuccess = () => {
    // Ingestion runs as a background task, so the new document may not be
    // aggregated from Qdrant yet; refresh now and once more shortly after.
    refreshDocs();
    setTimeout(refreshDocs, 3000);
  };

  const handleDeleteDoc = async (docId: string) => {
    await deleteDocument(docId);
    setDocs((prev) => prev.filter((doc) => doc.doc_id !== docId));
    setActiveDocId((prev) => (prev === docId ? null : prev));
  };

  const activeDoc = docs.find((doc) => doc.doc_id === activeDocId) ?? null;

  return (
    <div className="flex h-full w-full bg-bg">
      <Sidebar
        activeView={activeView}
        onNavigate={setActiveView}
        collapsed={collapsed}
        onToggle={() => setCollapsed(!collapsed)}
        docs={docs}
        onSelectDoc={(docId) => {
          setActiveDocId(docId);
          setActiveView("documents");
        }}
        healthOk={healthOk}
      />

      <main className="flex-1 flex flex-col overflow-hidden bg-surface">
        {activeView === "documents" && (
          <DocumentsView
            docs={docs}
            docsLoading={docsLoading}
            activeDocId={activeDocId}
            uploadOpen={uploadOpen}
            onUploadOpen={() => setUploadOpen(true)}
            onUploadClose={() => setUploadOpen(false)}
            onUploadSuccess={handleUploadSuccess}
            onSelectDoc={(docId) =>
              setActiveDocId((prev) => (prev === docId ? null : docId))
            }
            onDeleteDoc={handleDeleteDoc}
          />
        )}

        {activeView === "search" && <SearchView activeDoc={activeDoc} />}

        {activeView === "chat" && (
          // Remount on doc switch so an earlier answer grounded in a
          // different document is never mistaken for this one.
          <ChatView
            key={activeDocId ?? "all"}
            healthOk={healthOk}
            activeDoc={activeDoc}
          />
        )}
      </main>
    </div>
  );
}
