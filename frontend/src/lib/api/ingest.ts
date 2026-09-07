import type { IngestResponse, IngestTaskRecord } from "@/types/api";
import { apiFetch } from "./client";

export function ingestPDF(file: File): Promise<IngestResponse> {
  const body = new FormData();
  body.append("file", file);
  return apiFetch<IngestResponse>("/ingest", { method: "POST", body });
}

export function getIngestStatus(taskId: string): Promise<IngestTaskRecord> {
  return apiFetch<IngestTaskRecord>(`/ingest/${encodeURIComponent(taskId)}`);
}
