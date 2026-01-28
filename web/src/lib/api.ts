export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

// Prefix for versioned API
export const API_PREFIX = process.env.NEXT_PUBLIC_API_PREFIX ?? "/api/v1";

// Request timeout in milliseconds
const DEFAULT_TIMEOUT = 30000;
const RETRY_COUNT = 2;
const RETRY_DELAY = 1000;

// Simple in-memory cache
const cache = new Map<string, { data: unknown; timestamp: number }>();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

function hasDetail(x: unknown): x is { detail: unknown } {
  return typeof x === "object" && x !== null && "detail" in x;
}

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  const timeout = new Promise<never>((_, reject) =>
    setTimeout(() => reject(new Error("Request timeout")), ms)
  );
  return Promise.race([promise, timeout]);
}

async function withRetry<T>(
  fn: () => Promise<T>,
  retries: number = RETRY_COUNT,
  delay: number = RETRY_DELAY
): Promise<T> {
  try {
    return await fn();
  } catch (error) {
    if (retries > 0 && !(error instanceof ApiError && error.status < 500)) {
      await new Promise((resolve) => setTimeout(resolve, delay));
      return withRetry(fn, retries - 1, delay * 2);
    }
    throw error;
  }
}

export async function fetchJson<T>(
  path: string,
  init?: RequestInit & { cache?: boolean; timeout?: number }
): Promise<T> {
  const cacheKey = `GET:${path}`;
  const useCache = init?.cache !== false;
  const timeout = init?.timeout ?? DEFAULT_TIMEOUT;

  // Check cache for GET requests
  if (useCache && (!init?.method || init.method === "GET")) {
    const cached = cache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      return cached.data as T;
    }
  }

  const fetchFn = async () => {
    const res = await withTimeout(
      fetch(`${API_BASE_URL}${path}`, {
        ...init,
        headers: {
          "Content-Type": "application/json",
          ...init?.headers,
        },
      }),
      timeout
    );

    const data = (await res.json().catch(() => null)) as unknown;

    if (!res.ok) {
      const msg = hasDetail(data)
        ? String(data.detail)
        : `Request failed (${res.status})`;
      throw new ApiError(msg, res.status);
    }

    return data as T;
  };

  const result = await withRetry(fetchFn);

  // Cache successful GET responses
  if (useCache && (!init?.method || init.method === "GET")) {
    cache.set(cacheKey, { data: result, timestamp: Date.now() });
  }

  return result;
}

export async function postJson<T>(
  path: string,
  body: unknown,
  options?: { timeout?: number }
): Promise<T> {
  const timeout = options?.timeout ?? DEFAULT_TIMEOUT;

  const fetchFn = async () => {
    const res = await withTimeout(
      fetch(`${API_BASE_URL}${path}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      }),
      timeout
    );

    const data = (await res.json().catch(() => null)) as unknown;

    if (!res.ok) {
      const msg = hasDetail(data)
        ? String(data.detail)
        : `Request failed (${res.status})`;
      throw new ApiError(msg, res.status);
    }

    return data as T;
  };

  return withRetry(fetchFn);
}

export function clearCache(path?: string) {
  if (path) {
    cache.delete(`GET:${path}`);
  } else {
    cache.clear();
  }
}

export { ApiError };
