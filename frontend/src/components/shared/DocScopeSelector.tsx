"use client";

import { useEffect, useRef, useState } from "react";
import { Check, ChevronDown, FileText } from "lucide-react";
import type { Doc } from "@/types/document";

interface DocScopeSelectorProps {
  docs: Doc[];
  activeDoc: Doc | null;
  onSelect: (docId: string | null) => void;
}

export default function DocScopeSelector({
  docs,
  activeDoc,
  onSelect,
}: DocScopeSelectorProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("mousedown", handleClick);
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("mousedown", handleClick);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((prev) => !prev)}
        aria-haspopup="listbox"
        aria-expanded={open}
        className="flex items-center gap-2 px-3.5 py-2 rounded-lg border border-rim bg-bg-subtle text-sm font-medium text-ink hover:bg-rim/40 transition-colors max-w-[220px]"
      >
        <FileText className="w-4 h-4 flex-shrink-0 text-amber-dark" />
        <span className="truncate">
          {activeDoc ? activeDoc.source : "All documents"}
        </span>
        <ChevronDown className="w-3.5 h-3.5 flex-shrink-0 text-ink-subtle" />
      </button>

      {open && (
        <div
          role="listbox"
          className="absolute right-0 mt-2 w-64 max-h-72 overflow-y-auto bg-surface border border-rim rounded-lg shadow-[var(--shadow-raised)] z-10 py-1 animate-scale-in"
        >
          <button
            role="option"
            aria-selected={activeDoc === null}
            onClick={() => {
              onSelect(null);
              setOpen(false);
            }}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-left text-ink hover:bg-bg-subtle transition-colors"
          >
            <span className="w-4 flex-shrink-0">
              {activeDoc === null && <Check className="w-4 h-4 text-amber" />}
            </span>
            All documents
          </button>
          <div className="my-1 border-t border-rim" />
          {docs.map((doc) => (
            <button
              key={doc.doc_id}
              role="option"
              aria-selected={activeDoc?.doc_id === doc.doc_id}
              onClick={() => {
                onSelect(doc.doc_id);
                setOpen(false);
              }}
              title={doc.source}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-left text-ink hover:bg-bg-subtle transition-colors"
            >
              <span className="w-4 flex-shrink-0">
                {activeDoc?.doc_id === doc.doc_id && (
                  <Check className="w-4 h-4 text-amber" />
                )}
              </span>
              <span className="truncate">{doc.source}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
