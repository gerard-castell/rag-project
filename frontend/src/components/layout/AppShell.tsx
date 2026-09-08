"use client";

import { useState } from "react";
import { Menu } from "lucide-react";
import { useDocuments } from "@/contexts/documents-context";
import DocumentsView from "@/components/documents/DocumentsView";
import SearchPanel from "@/components/search/SearchPanel";
import ChatPanel from "@/components/chat/ChatPanel";
import UploadModal from "@/components/upload/UploadModal";
import Sidebar from "./Sidebar";

type ActiveView = "documents" | "search" | "chat";

export default function AppShell() {
  const [activeView, setActiveView] = useState<ActiveView>("documents");
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const { activeDocId } = useDocuments();

  return (
    <div className="flex h-full w-full bg-bg">
      <Sidebar
        activeView={activeView}
        onNavigate={setActiveView}
        mobileOpen={mobileNavOpen}
        onMobileClose={() => setMobileNavOpen(false)}
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile top bar */}
        <div className="md:hidden flex items-center gap-3 px-4 h-14 border-b border-rim bg-surface flex-shrink-0">
          <button
            onClick={() => setMobileNavOpen(true)}
            aria-label="Open navigation"
            className="p-1.5 -ml-1.5 rounded-lg hover:bg-bg-subtle focus:outline-none focus-visible:ring-2 focus-visible:ring-amber"
          >
            <Menu className="w-5 h-5 text-ink" />
          </button>
          <span className="font-serif font-bold text-ink tracking-tight">Papyr</span>
        </div>

        <main className="flex-1 flex flex-col overflow-hidden bg-surface">
          {activeView === "documents" && <DocumentsView />}
          {activeView === "search" && <SearchPanel />}
          {activeView === "chat" && (
            // Remount on doc switch so an earlier answer grounded in a
            // different document is never mistaken for this one.
            <ChatPanel key={activeDocId ?? "all"} />
          )}
        </main>
      </div>

      <UploadModal />
    </div>
  );
}
