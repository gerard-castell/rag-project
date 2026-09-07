"use client";

import { useState } from "react";
import { Plus, Search as SearchIcon } from "lucide-react";
import { search } from "@/lib/api";
import type { SearchResult } from "@/types/api";
import { useDocuments } from "@/contexts/documents-context";
import { useUploadModal } from "@/contexts/upload-modal-context";
import DocScopeSelector from "@/components/shared/DocScopeSelector";
import PageHeader from "@/components/shared/PageHeader";

export default function SearchPanel() {
  const { docs, activeDoc, selectDoc } = useDocuments();
  const { open: openUpload } = useUploadModal();
  const hasDocs = docs.length > 0;
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    search(query, 5, activeDoc?.doc_id)
      .then((data) => setResults(data))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Search failed. Try again.");
        setResults([]);
      })
      .finally(() => setLoading(false));
  };

  return (
    <>
      <PageHeader
        icon={SearchIcon}
        title="Search"
        subtitle={
          activeDoc ? `Scoped to: ${activeDoc.source}` : "Searching all documents"
        }
        action={
          hasDocs && (
            <DocScopeSelector
              docs={docs}
              activeDoc={activeDoc}
              onSelect={selectDoc}
            />
          )
        }
      />

      {/* Content */}
      <div className="flex-1 overflow-auto p-8">
        {/* Search form */}
        <div className="mb-8 max-w-2xl">
          <p className="mb-3 text-sm text-ink-subtle">
            Shows the exact passages from your documents that match your
            query, ranked by relevance.
          </p>
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <SearchIcon className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-subtle pointer-events-none" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSearch();
                }}
                placeholder="Search documents..."
                aria-label="Search query"
                className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-rim bg-bg-subtle text-ink placeholder-ink-subtle focus:outline-none focus:ring-2 focus:ring-amber focus:border-transparent transition-shadow"
              />
            </div>
            <button
              onClick={handleSearch}
              disabled={loading || !query.trim()}
              className="px-6 py-2.5 rounded-lg bg-amber text-white font-medium shadow-[var(--shadow-card)] hover:bg-amber-dark hover:shadow-[var(--shadow-card-hover)] active:scale-[0.98] disabled:opacity-50 disabled:shadow-none disabled:active:scale-100 transition-all"
            >
              {loading ? "Searching..." : "Search"}
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 max-w-2xl p-4 bg-danger-soft text-danger rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* Results loading skeleton */}
        {loading && (
          <div className="max-w-2xl space-y-4" aria-busy="true" aria-label="Searching">
            {Array.from({ length: 3 }).map((_, idx) => (
              <div
                key={idx}
                className="p-4 bg-surface rounded-lg border border-rim animate-pulse"
              >
                <div className="h-3 w-1/3 bg-bg-subtle rounded mb-3" />
                <div className="h-3 w-full bg-bg-subtle rounded mb-2" />
                <div className="h-3 w-5/6 bg-bg-subtle rounded" />
              </div>
            ))}
          </div>
        )}

        {/* Results */}
        {!loading && results.length > 0 && (
          <div className="max-w-2xl space-y-4 animate-scale-in">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-ink-subtle mb-4">
              {results.length} result{results.length !== 1 ? "s" : ""}
            </h2>
            {results.map((result, idx) => (
              <div
                key={idx}
                className="relative pl-4 p-4 bg-surface rounded-lg border border-rim shadow-[var(--shadow-card)] hover:shadow-[var(--shadow-card-hover)] transition-shadow"
              >
                <div
                  className="absolute left-0 top-3 bottom-3 w-1 rounded-full bg-amber"
                  style={{ opacity: Math.max(result.score, 0.25) }}
                />
                <div className="text-xs text-ink-muted mb-2 flex flex-wrap gap-x-4 gap-y-1">
                  <span className="font-semibold text-amber-dark">
                    {(result.score * 100).toFixed(0)}% match
                  </span>
                  {result.metadata.source != null && (
                    <span>{result.metadata.source}</span>
                  )}
                  {result.metadata.page != null && (
                    <span>Page {result.metadata.page}</span>
                  )}
                </div>
                <p className="text-ink leading-relaxed">{result.text}</p>
              </div>
            ))}
          </div>
        )}

        {/* Empty state */}
        {!loading && results.length === 0 && !error && !hasDocs && (
          <div className="flex flex-col items-center text-center py-16">
            <div className="w-16 h-16 rounded-full bg-amber-soft flex items-center justify-center mb-4">
              <SearchIcon className="w-7 h-7 text-amber-dark" strokeWidth={1.5} />
            </div>
            <p className="text-ink font-medium">Upload a PDF to start searching</p>
            <p className="text-sm text-ink-subtle mt-1 mb-5">
              Search across your documents once one is indexed
            </p>
            <button
              onClick={openUpload}
              className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-amber text-white font-medium shadow-[var(--shadow-card)] hover:bg-amber-dark hover:shadow-[var(--shadow-card-hover)] active:scale-[0.98] transition-all"
            >
              <Plus className="w-4 h-4" />
              Upload your first PDF
            </button>
          </div>
        )}

        {!loading && results.length === 0 && !error && hasDocs && (
          <div className="flex flex-col items-center text-center py-16">
            <div className="w-16 h-16 rounded-full bg-amber-soft flex items-center justify-center mb-4">
              <SearchIcon className="w-7 h-7 text-amber-dark" strokeWidth={1.5} />
            </div>
            <p className="text-ink font-medium">
              {query.trim() ? "No results found" : "Start searching to see results"}
            </p>
            <p className="text-sm text-ink-subtle mt-1">
              {query.trim()
                ? "Try a different phrase, or check the document scope above."
                : "Type a word or phrase to find matching passages in your documents."}
            </p>
          </div>
        )}
      </div>
    </>
  );
}
