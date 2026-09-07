import type { HealthResponse } from "@/types/api";
import { apiFetch } from "./client";

export function health(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health");
}
