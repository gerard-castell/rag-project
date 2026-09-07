import { FileText, Search, MessageSquare, type LucideIcon } from "lucide-react";
import { useDocuments } from "@/contexts/documents-context";
import { useHealth } from "@/contexts/health-context";

type ActiveView = "documents" | "search" | "chat";

interface SidebarProps {
  activeView: ActiveView;
  onNavigate: (view: ActiveView) => void;
}

const navItems: { id: ActiveView; icon: LucideIcon; label: string }[] = [
  { id: "documents", icon: FileText, label: "Documents" },
  { id: "search", icon: Search, label: "Search" },
  { id: "chat", icon: MessageSquare, label: "Chat" },
];

export default function Sidebar({ activeView, onNavigate }: SidebarProps) {
  const { docs, selectDoc } = useDocuments();
  const healthOk = useHealth();

  return (
    <div className="flex flex-col h-full w-60 bg-surface border-r border-rim">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-4 h-16 border-b border-rim">
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-ink flex items-center justify-center">
          <span className="font-serif font-bold text-sm text-amber-soft">P</span>
        </div>
        <div className="font-serif font-bold text-lg text-ink tracking-tight">
          Papyr
        </div>
      </div>

      {/* Nav items */}
      <nav className="flex-1 px-2.5 py-4 space-y-0.5" aria-label="Primary">
        {navItems.map(({ id, icon: Icon, label }) => {
          const active = activeView === id;
          return (
            <button
              key={id}
              onClick={() => onNavigate(id)}
              aria-current={active ? "page" : undefined}
              className={`relative w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-amber ${
                active
                  ? "bg-amber-soft text-amber-dark"
                  : "text-ink-muted hover:bg-bg-subtle hover:text-ink"
              }`}
            >
              {active && (
                <span className="absolute left-0 top-1.5 bottom-1.5 w-0.5 rounded-full bg-amber" />
              )}
              <Icon className="w-[18px] h-[18px] flex-shrink-0" />
              {label}
            </button>
          );
        })}
      </nav>

      {/* Recent docs */}
      {docs.length > 0 && (
        <div className="px-4 py-4 border-t border-rim">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-ink-subtle mb-2.5">
            Recent
          </div>
          <div className="space-y-0.5 max-h-32 overflow-y-auto">
            {docs.slice(0, 4).map((doc) => (
              <button
                key={doc.doc_id}
                onClick={() => {
                  selectDoc(doc.doc_id);
                  onNavigate("documents");
                }}
                title={doc.source}
                className="w-full flex items-center px-2 py-1.5 text-xs text-ink-muted truncate hover:text-ink hover:bg-bg-subtle rounded-md transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-amber"
              >
                <FileText className="w-3 h-3 inline mr-1.5 text-amber flex-shrink-0" />
                <span className="truncate">{doc.source}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Status */}
      <div className="border-t border-rim">
        <div className="flex items-center gap-2 px-4 py-3 text-xs text-ink-subtle">
          <span
            className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
              healthOk ? "bg-success" : "bg-danger"
            }`}
          />
          {healthOk ? "Backend connected" : "Backend unavailable"}
        </div>
      </div>
    </div>
  );
}
