import {
  FileText,
  Search,
  MessageSquare,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Doc } from "./AppShell";

type ActiveView = "documents" | "search" | "chat";

interface SidebarProps {
  activeView: ActiveView;
  onNavigate: (view: ActiveView) => void;
  collapsed: boolean;
  onToggle: () => void;
  docs: Doc[];
}

const navItems: Array<{ id: ActiveView; icon: typeof FileText; label: string }> =
  [
    { id: "documents", icon: FileText, label: "Documents" },
    { id: "search", icon: Search, label: "Search" },
    { id: "chat", icon: MessageSquare, label: "Chat" },
  ];

export default function Sidebar({
  activeView,
  onNavigate,
  collapsed,
  onToggle,
  docs,
}: SidebarProps) {
  return (
    <div
      className={`flex flex-col h-full bg-surface border-r border-rim transition-all duration-300 ${
        collapsed ? "w-14" : "w-56"
      }`}
    >
      {/* Logo */}
      <div className="px-4 py-6 border-b border-rim">
        {!collapsed && (
          <div className="font-serif font-bold text-lg text-ink">Papyr</div>
        )}
      </div>

      {/* Nav items */}
      <nav className="flex-1 px-2 py-4 space-y-1">
        {navItems.map(({ id, icon: Icon, label }) => (
          <button
            key={id}
            onClick={() => onNavigate(id)}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeView === id
                ? "bg-amber-soft text-amber"
                : "text-ink-muted hover:bg-bg-subtle"
            }`}
          >
            <Icon className="w-5 h-5 flex-shrink-0" />
            {!collapsed && label}
          </button>
        ))}
      </nav>

      {/* Recent docs (collapsed view hides this) */}
      {!collapsed && docs.length > 0 && (
        <div className="px-4 py-4 border-t border-rim">
          <div className="text-xs font-medium uppercase tracking-wider text-ink-subtle mb-3">
            Recent
          </div>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {docs.slice(0, 4).map((doc) => (
              <div
                key={doc.doc_id}
                className="px-2 py-1 text-xs text-ink-muted truncate hover:text-ink cursor-pointer transition-colors"
                title={doc.source}
              >
                <FileText className="w-3 h-3 inline mr-1 text-amber" />
                {doc.source}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Collapse toggle */}
      <div className="px-2 py-4 border-t border-rim">
        <button
          onClick={onToggle}
          className="w-full p-2 hover:bg-bg-subtle rounded-lg transition-colors"
          title={collapsed ? "Expand" : "Collapse"}
        >
          {collapsed ? (
            <ChevronRight className="w-5 h-5 text-ink-muted mx-auto" />
          ) : (
            <ChevronLeft className="w-5 h-5 text-ink-muted mx-auto" />
          )}
        </button>
      </div>
    </div>
  );
}
