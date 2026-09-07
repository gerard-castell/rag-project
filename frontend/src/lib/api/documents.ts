import type { Doc } from "@/types/document";
import { apiFetch } from "./client";

export function listDocuments(): Promise<Doc[]> {
  return apiFetch<Doc[]>("/documents");
}

export function deleteDocument(docId: string): Promise<void> {
  return apiFetch<void>(`/documents/${encodeURIComponent(docId)}`, {
    method: "DELETE",
  });
}
