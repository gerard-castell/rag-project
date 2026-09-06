import type { LucideIcon } from "lucide-react";

interface PageHeaderProps {
  icon: LucideIcon;
  title: string;
  subtitle?: React.ReactNode;
  action?: React.ReactNode;
}

export default function PageHeader({
  icon: Icon,
  title,
  subtitle,
  action,
}: PageHeaderProps) {
  return (
    <div className="flex items-center justify-between gap-4 px-6 h-16 border-b border-rim bg-surface/80 backdrop-blur-sm">
      <div className="flex items-center gap-2.5 min-w-0">
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-amber-soft flex items-center justify-center">
          <Icon className="w-4 h-4 text-amber-dark" />
        </div>
        <div className="min-w-0">
          <h1 className="text-lg font-serif font-bold text-ink tracking-tight truncate">
            {title}
          </h1>
          {subtitle && (
            <p className="text-xs text-ink-subtle truncate">{subtitle}</p>
          )}
        </div>
      </div>
      {action && <div className="flex-shrink-0">{action}</div>}
    </div>
  );
}
