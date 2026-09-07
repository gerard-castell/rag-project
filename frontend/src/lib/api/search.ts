import type { SearchResult } from "@/types/api";
import { apiJsonFetch } from "./client";

export function search(
  query: string,
  limit = 5,
  docId?: string | null
): Promise<SearchResult[]> {
  return apiJsonFetch<SearchResult[]>("/search", {
    query,
    limit,
    doc_id: docId ?? null,
  });
}
