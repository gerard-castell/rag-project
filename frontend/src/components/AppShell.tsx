"use client";

import { useState, useEffect, useRef } from "react";
import { getIngestStatus, health } from "@/lib/api";
import Sidebar from "./Sidebar";
import DocumentsView from "./DocumentsView";
import SearchView from "./SearchPanel";
import ChatView from "./ChatPanel";

export type DocStatus = "processing" | "indexed" | "error";

export interface Doc {
  id: string;
  name: string;
  uploadedAt: Date;
  status: DocStatus;
  error?: string;
}

type ActiveView = "documents" | "search" | "chat";

const POLL_INTERVAL_MS = 2000;

export default function AppShell() {
  const [activeView, setActiveView] = useState<ActiveView>("documents");
  const [docs, setDocs] = useState<Doc[]>([]);
  const [collapsed, setCollapsed] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [healthOk, setHealthOk] = useState(false);
  const pollingIds = useRef(new Set<string>());

  useEffect(() => {
    health()
      .then(() => setHealthOk(true))
      .catch(() => setHealthOk(false));
  }, []);

  useEffect(() => {
    const processingDocs = docs.filter((doc) => doc.status === "processing");
    if (processingDocs.length === 0) return;

    const interval = setInterval(async () => {
      for (const doc of processingDocs) {
        if (pollingIds.current.has(doc.id)) continue;
        pollingIds.current.add(doc.id);
        try {
          const record = await getIngestStatus(doc.id);
          if (record.status === "done") {
            setDocs((prev) =>
              prev.map((d) =>
                d.id === doc.id ? { ...d, status: "indexed" } : d
              )
            );
          } else if (record.status === "failed") {
            setDocs((prev) =>
              prev.map((d) =>
                d.id === doc.id
                  ? {
                      ...d,
                      status: "error",
                      error: record.error ?? "Ingestion failed.",
                    }
                  : d
              )
            );
          }
        } catch {
          // Transient poll failure; retry on the next tick.
        } finally {
          pollingIds.current.delete(doc.id);
        }
      }
    }, POLL_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [docs]);

  const addDoc = (name: string, taskId: string) => {
    setDocs((prev) => [
      ...prev,
      { id: taskId, name, uploadedAt: new Date(), status: "processing" },
    ]);
  };

  return (
    <div className="flex h-full w-full bg-bg">
      <Sidebar
        activeView={activeView}
        onNavigate={setActiveView}
        collapsed={collapsed}
        onToggle={() => setCollapsed(!collapsed)}
        docs={docs}
      />

      <main className="flex-1 flex flex-col overflow-hidden bg-surface">
        {activeView === "documents" && (
          <DocumentsView
            docs={docs}
            uploadOpen={uploadOpen}
            onUploadOpen={() => setUploadOpen(true)}
            onUploadClose={() => setUploadOpen(false)}
            onAddDoc={addDoc}
          />
        )}

        {activeView === "search" && <SearchView />}

        {activeView === "chat" && <ChatView healthOk={healthOk} />}
      </main>
    </div>
  );
}
