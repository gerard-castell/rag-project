import type { ChatResponse } from "@/types/api";
import { ApiError, apiJsonFetch } from "./client";

export class ModelWarmingUpError extends Error {}

export async function chat(
  message: string,
  docId?: string | null
): Promise<ChatResponse> {
  try {
    return await apiJsonFetch<ChatResponse>("/chat", {
      message,
      max_tokens: 512,
      temperature: 0.7,
      doc_id: docId ?? null,
    });
  } catch (err) {
    if (err instanceof ApiError && err.status === 503) {
      throw new ModelWarmingUpError(err.message);
    }
    throw err;
  }
}
