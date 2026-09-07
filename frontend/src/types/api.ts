export interface IngestResponse {
  status: string;
  task_id: string;
  info: string;
}

export type IngestTaskStatus =
  | "queued"
  | "parsing"
  | "embedding"
  | "done"
  | "failed";

export interface IngestTaskRecord {
  status: IngestTaskStatus;
  chunks_indexed: number;
  total_chunks: number;
  error: string | null;
}

export interface SearchResult {
  text: string;
  score: number;
  metadata: Record<string, string | number | boolean | null>;
}

export interface ChatResponse {
  response: string;
  model: string;
  total_duration_ms: number | null;
  context_chunks_used: number | null;
}

export interface HealthResponse {
  status: string;
  device: string;
}
