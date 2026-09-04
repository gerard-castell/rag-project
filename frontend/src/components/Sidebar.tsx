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
  onSelectDoc: (docId: string) => void;
  healthOk: boolean;
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
  onSelectDoc,
  healthOk,
}: SidebarProps) {
  return (
    <div
      className={`flex flex-col h-full bg-surface border-r border-rim transition-[width] duration-300 ${
        collapsed ? "w-16" : "w-60"
      }`}
    >
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-4 h-16 border-b border-rim">
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-ink flex items-center justify-center">
          <span className="font-serif font-bold text-sm text-amber-soft">P</span>
        </div>
        {!collapsed && (
          <>
            <div className="font-serif font-bold text-lg text-ink tracking-tight">
              Papyr
            </div>
            <button
              onClick={onToggle}
              aria-label="Collapse sidebar"
              className="ml-auto flex-shrink-0 p-0.5 text-ink-subtle hover:text-ink transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-amber rounded"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
          </>
        )}
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
              title={collapsed ? label : undefined}
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
              {!collapsed && label}
            </button>
          );
        })}
      </nav>

      {/* Recent docs (collapsed view hides this) */}
      {!collapsed && docs.length > 0 && (
        <div className="px-4 py-4 border-t border-rim">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-ink-subtle mb-2.5">
            Recent
          </div>
          <div className="space-y-0.5 max-h-32 overflow-y-auto">
            {docs.slice(0, 4).map((doc) => (
              <button
                key={doc.doc_id}
                onClick={() => onSelectDoc(doc.doc_id)}
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

      {/* Status + collapse toggle */}
      <div className="border-t border-rim">
        {!collapsed && (
          <div className="flex items-center gap-2 px-4 py-3 text-xs text-ink-subtle">
            <span
              className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                healthOk ? "bg-success" : "bg-danger"
              }`}
            />
            {healthOk ? "Backend connected" : "Backend unavailable"}
          </div>
        )}
        {collapsed && (
          <div className="pb-3 flex justify-center">
            <button
              onClick={onToggle}
              aria-label="Expand sidebar"
              className="p-0.5 text-ink-subtle hover:text-ink transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-amber rounded"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
