"use client";

import { useState } from "react";
import { Search as SearchIcon } from "lucide-react";
import { search, SearchResult } from "@/lib/api";
import { Doc } from "./AppShell";

interface SearchPanelProps {
  activeDoc: Doc | null;
}

export default function SearchPanel({ activeDoc }: SearchPanelProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const data = await search(query, 5, activeDoc?.doc_id);
      setResults(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Search failed. Try again."
      );
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Header */}
      <div className="px-8 py-6 border-b border-rim bg-surface">
        <h1 className="text-2xl font-serif font-bold text-ink">Search</h1>
        <p className="text-sm text-ink-subtle mt-1">
          {activeDoc ? `Scoped to: ${activeDoc.source}` : "Searching all documents"}
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-8">
        {/* Search form */}
        <div className="mb-8 max-w-2xl">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSearch();
                }}
                placeholder="Search documents..."
                className="w-full px-4 py-2 rounded-lg border border-rim bg-bg-subtle text-ink placeholder-ink-subtle focus:outline-none focus:ring-2 focus:ring-accent"
              />
              <SearchIcon className="absolute right-3 top-2.5 w-5 h-5 text-ink-muted pointer-events-none" />
            </div>
            <button
              onClick={handleSearch}
              disabled={loading || !query.trim()}
              className="px-6 py-2 rounded-lg bg-accent text-white font-medium hover:bg-accent-dark disabled:opacity-50 transition-colors"
            >
              {loading ? "Searching..." : "Search"}
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 p-4 bg-danger-soft text-danger rounded-lg">
            {error}
          </div>
        )}

        {/* Results */}
        {results.length > 0 && (
          <div className="max-w-2xl space-y-4">
            <h2 className="font-medium text-ink mb-4">
              {results.length} result{results.length !== 1 ? "s" : ""}
            </h2>
            {results.map((result, idx) => (
              <div key={idx} className="p-4 bg-surface rounded-lg border border-rim">
                <div className="text-sm text-ink-muted mb-2 flex gap-4">
                  <span className="font-medium">
                    Score: {(result.score * 100).toFixed(0)}%
                  </span>
                  {result.metadata && (
                    <>
                      {result.metadata.source && (
                        <span>Source: {result.metadata.source}</span>
                      )}
                      {result.metadata.page && <span>Page {result.metadata.page}</span>}
                    </>
                  )}
                </div>
                <p className="text-ink leading-relaxed">{result.text}</p>
              </div>
            ))}
          </div>
        )}

        {/* Empty state */}
        {!loading && results.length === 0 && !error && (
          <div className="text-center text-ink-subtle">
            <p className="text-lg">
              {query.trim() ? "No results found" : "Start searching to see results"}
            </p>
          </div>
        )}
      </div>
    </>
  );
}
