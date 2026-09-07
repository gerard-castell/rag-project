const BASE = "/api";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function readErrorMessage(res: Response): Promise<string> {
  const text = await res.text().catch(() => "");
  return text || res.statusText;
}

interface ApiRequestInit {
  method?: string;
  headers?: Record<string, string>;
  body?: BodyInit;
}

/** Thin fetch wrapper: resolves relative to the backend proxy, throws ApiError on non-2xx. */
export async function apiFetch<T>(
  path: string,
  init: ApiRequestInit = {}
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    throw new ApiError(await readErrorMessage(res), res.status);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

export function apiJsonFetch<T>(
  path: string,
  body: unknown,
  method = "POST"
): Promise<T> {
  return apiFetch<T>(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
