"use client";

import { useState } from "react";
import { useDocuments } from "@/contexts/documents-context";
import DocumentsView from "@/components/documents/DocumentsView";
import SearchPanel from "@/components/search/SearchPanel";
import ChatPanel from "@/components/chat/ChatPanel";
import UploadModal from "@/components/upload/UploadModal";
import Sidebar from "./Sidebar";

type ActiveView = "documents" | "search" | "chat";

export default function AppShell() {
  const [activeView, setActiveView] = useState<ActiveView>("documents");
  const { activeDocId } = useDocuments();

  return (
    <div className="flex h-full w-full bg-bg">
      <Sidebar activeView={activeView} onNavigate={setActiveView} />

      <main className="flex-1 flex flex-col overflow-hidden bg-surface">
        {activeView === "documents" && <DocumentsView />}
        {activeView === "search" && <SearchPanel />}
        {activeView === "chat" && (
          // Remount on doc switch so an earlier answer grounded in a
          // different document is never mistaken for this one.
          <ChatPanel key={activeDocId ?? "all"} />
        )}
      </main>

      <UploadModal />
    </div>
  );
}
