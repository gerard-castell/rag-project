"use client";

import { useState, useEffect } from "react";
import { health } from "@/lib/api";
import Sidebar from "./Sidebar";
import DocumentsView from "./DocumentsView";
import SearchView from "./SearchPanel";
import ChatView from "./ChatPanel";

export interface Doc {
  id: string;
  name: string;
  uploadedAt: Date;
}

type ActiveView = "documents" | "search" | "chat";

export default function AppShell() {
  const [activeView, setActiveView] = useState<ActiveView>("documents");
  const [docs, setDocs] = useState<Doc[]>([]);
  const [collapsed, setCollapsed] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [healthOk, setHealthOk] = useState(false);

  useEffect(() => {
    health()
      .then(() => setHealthOk(true))
      .catch(() => setHealthOk(false));
  }, []);

  const addDoc = (name: string, taskId: string) => {
    setDocs((prev) => [
      ...prev,
      { id: taskId, name, uploadedAt: new Date() },
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
