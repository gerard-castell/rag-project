const BASE = "/api";

export interface IngestResponse {
  status: string;
  task_id: string;
  info: string;
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

export async function ingestPDF(file: File): Promise<IngestResponse> {
  const body = new FormData();
  body.append("file", file);
  const res = await fetch(`${BASE}/ingest`, { method: "POST", body });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<IngestResponse>;
}

export async function search(
  query: string,
  limit = 5
): Promise<SearchResult[]> {
  const res = await fetch(`${BASE}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, limit }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<SearchResult[]>;
}

export async function chat(message: string): Promise<ChatResponse> {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, max_tokens: 512, temperature: 0.7 }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<ChatResponse>;
}

export async function health(): Promise<HealthResponse> {
  const res = await fetch(`${BASE}/health`);
  if (!res.ok) throw new Error(res.statusText);
  return res.json() as Promise<HealthResponse>;
}
